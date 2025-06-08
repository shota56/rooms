import os
import io
import time
import base64
import random
import logging
import requests
from PIL import Image
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# APIキーの取得
STABILITY_API_KEY = os.getenv('STABILITY_API_KEY')
if not STABILITY_API_KEY:
    raise ValueError("STABILITY_API_KEY環境変数が設定されていません")

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Flaskアプリケーションの初期化
app = Flask(__name__, static_folder='public')
CORS(app)  # CORS対応

# 生成された画像を保存するディレクトリ
images_dir = os.path.join(app.static_folder, 'generated-images')
os.makedirs(images_dir, exist_ok=True)

# 画像ディレクトリの設定を追加
styles_images_dir = os.path.join(app.static_folder, 'images', 'styles')
os.makedirs(styles_images_dir, exist_ok=True)

# スタイルごとの詳細な指示を定義
STYLE_DETAILS = {
   "simple": {
    "main": "modern minimalist interior style, uncluttered and streamlined design",
    "colors": "bright white walls, subtle gray touches, neutral monochrome palette",
    "materials": "sleek surfaces, pale wood finishes, matte textures",
    "furniture": "essential furniture only, straight lines, multifunctional design",
    "lighting": "minimalist pendant lights, large windows, natural daylight",
    "mood": "peaceful, orderly, refreshing minimal space"
},
"scandinavian": {
    "main": "nordic-inspired scandinavian interior, inviting and balanced",
    "colors": "crisp white walls, blonde wood, soft grays, gentle pastels",
    "materials": "oak flooring, cozy textiles, painted wood finishes",
    "furniture": "light wood furniture, soft fabrics, playful modern shapes",
    "lighting": "ample daylight, contemporary pendants, warm soft glow",
    "mood": "bright, tranquil, welcoming nordic comfort"
},
"hotel": {
  "main": "hotel-inspired modern interior, elegant and comfort-focused design",
  "colors": "neutral tones like beige, white, and taupe, with soft accent colors",
  "materials": "high-quality fabrics, polished wood, glass, and metal finishes",
  "furniture": "coordinated furniture sets, upholstered headboard, sleek desk and armchair",
  "lighting": "layered lighting with warm tones, bedside lamps, sconces, and natural light",
  "mood": "calm, luxurious, welcoming, like a premium hotel suite"
},
"korean": {
    "main": "contemporary korean interior, sleek and modern asian design",
    "colors": "creamy whites, muted grays, earthy accents, dark contrasts",
    "materials": "light-toned woods, textured wall panels, smooth stone",
    "furniture": "low minimalist furniture, streamlined storage, built-ins",
    "lighting": "subtle ceiling lights, soft indirect glow",
    "mood": "fashionable, serene, understated korean refinement"
},
"brooklyn": {
    "main": "industrial brooklyn loft, urban apartment conversion",
    "colors": "weathered brick red, concrete gray, black metal details",
    "materials": "exposed brick, steel pipes, reclaimed wood surfaces",
    "furniture": "industrial style pieces, vintage decor, worn-in leather",
    "lighting": "caged pendant lights, exposed bulbs, utilitarian fixtures",
    "mood": "gritty, urban, creative industrial vibe"
},
"natural": {
    "main": "nature-inspired organic interior, biophilic oasis",
    "colors": "earthy tans, leafy greens, soft wood tones",
    "materials": "raw wood, natural stone, woven textiles, living plants",
    "furniture": "nature-shaped wood furniture, handwoven fabrics, eco-focused pieces",
    "lighting": "floor-to-ceiling windows, sunlit interiors, warm spot lighting",
    "mood": "calm, earthy, deeply connected to the natural world"
},
"japanese_modern": {
    "main": "contemporary japanese zen interior, modern simplicity",
    "colors": "gentle whites, honey wood grains, charcoal highlights",
    "materials": "shoji screens, tatami flooring, authentic woodwork",
    "furniture": "low tables, minimalist built-ins, hidden storage",
    "lighting": "lantern-style lamps, subtle indirect light, soft daylight",
    "mood": "contemplative, balanced, serene japanese minimalism"
},
"ethnic_mix": {
    "main": "eclectic world-inspired ethnic fusion interiors",
    "colors": "vivid jewel colors, spicy warm hues, natural earthy tones",
    "materials": "handcrafted textiles, ornate wood carvings, organic fibers",
    "furniture": "global mix of artisanal furniture, one-of-a-kind objects",
    "lighting": "ethnic pendant lanterns, soft colored lamps, glowing atmosphere",
    "mood": "adventurous, multicultural, artistically rich"
}
    }

# 簡易翻訳機能（日本語→英語の主要な部屋関連単語）
def translate_text(text, dest='en'):
    """簡易的な翻訳機能（日本語→英語）"""
    # 部屋関連の日本語→英語の辞書
    ja_to_en = {
        "壁": "wall",
        "床": "floor",
        "天井": "ceiling",
        "窓": "window",
        "ドア": "door",
        "家具": "furniture",
        "ソファ": "sofa",
        "テーブル": "table",
        "椅子": "chair",
        "ベッド": "bed",
        "照明": "lighting",
        "ランプ": "lamp",
        "カーテン": "curtain",
        "カーペット": "carpet",
        "ラグ": "rug",
        "棚": "shelf",
        "本棚": "bookshelf",
        "キッチン": "kitchen",
        "バスルーム": "bathroom",
        "リビング": "living room",
        "ダイニング": "dining room",
        "寝室": "bedroom",
        "オフィス": "office",
        "モダン": "modern",
        "ミニマル": "minimal",
        "ラグジュアリー": "luxury",
        "北欧": "scandinavian",
        "インダストリアル": "industrial",
        "伝統的": "traditional",
        "居心地の良い": "cozy",
        "ナチュラル": "natural",
        "青": "blue",
        "赤": "red",
        "緑": "green",
        "黄色": "yellow",
        "白": "white",
        "黒": "black",
        "グレー": "gray",
        "茶色": "brown",
        "木製": "wooden",
        "金属": "metal",
        "ガラス": "glass",
        "大理石": "marble",
        "コンクリート": "concrete",
        "レンガ": "brick",
        "に変更": "change to",
        "にする": "make it"
    }
    
    # 入力テキストを単語に分割して翻訳
    translated = text
    for ja, en in ja_to_en.items():
        translated = translated.replace(ja, en)
    
    logger.info(f"翻訳: '{text}' → '{translated}'")
    return translated

# 静的ファイルの提供
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(app.static_folder, path)

@app.route('/generated-images/<path:filename>')
def generated_image(filename):
    return send_from_directory(images_dir, filename)

# 静的ファイルのルートを追加
@app.route('/images/styles/<path:filename>')
def style_image(filename):
    return send_from_directory(styles_images_dir, filename)

# 部屋のスタイルリストを提供するAPI
@app.route('/api/room-styles')
def get_room_styles():
    """部屋のスタイルリストを返す"""
    styles = [
        {
            "id": "simple",
            "name": "シンプル",
            "image": "/images/styles/simple.jpg"
        },
        {
            "id": "scandinavian",
            "name": "北欧風",
            "image": "/images/styles/scandinavian.jpg"
        },
        {
            "id": "hotel",
            "name": "ホテルライク",
            "image": "/images/styles/hotel.jpg"
        },
        {
            "id": "korean",
            "name": "韓国風",
            "image": "/images/styles/korean.jpg"
        },
        {
            "id": "brooklyn",
            "name": "ブルックリンスタイル",
            "image": "/images/styles/brooklyn.jpg"
        },
        {
            "id": "natural",
            "name": "ナチュラル",
            "image": "/images/styles/natural.jpg"
        },
        {
            "id": "japanese_modern",
            "name": "和モダン",
            "image": "/images/styles/japanese_modern.jpg"
        },
        {
            "id": "ethnic_mix",
            "name": "エスニックミックス",
            "image": "/images/styles/ethnic_mix.jpg"
        }
    ]
    return jsonify(styles)

@app.route('/api/transform-room-style', methods=['POST'])
def transform_room_style():
    try:
        data = request.json
        image_data = data.get('imageData')
        style = data.get('style')
        
        if not image_data:
            return jsonify({'error': '画像データが必要です'}), 400
        
        if not style:
            return jsonify({'error': 'スタイルが必要です'}), 400
        
        logger.info('部屋のスタイル変更リクエスト受信')
        logger.info('選択されたスタイル: %s', style)
        
        try:
            # Base64のヘッダー部分を削除
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            img = Image.open(io.BytesIO(image_bytes))
            
            # 元の画像を保存
            timestamp = int(time.time())
            original_filename = f'original-{timestamp}.png'
            original_path = os.path.join(images_dir, original_filename)
            img.save(original_path, format="PNG", quality=95)
            
            logger.info('元の画像を保存: %s', original_path)
            
            # アスペクト比を保持しながら、許可されているサイズに変換
            original_aspect_ratio = img.width / img.height
            
            # 許可されているサイズのリスト
            allowed_sizes = [
                (1024, 1024),
                (1152, 896),
                (1216, 832),
                (1344, 768),
                (1536, 640),
                (640, 1536),
                (768, 1344),
                (832, 1216),
                (896, 1152)
            ]
            
            # 最適なサイズを選択
            def get_aspect_ratio_difference(size):
                return abs((size[0] / size[1]) - original_aspect_ratio)
            
            target_size = min(allowed_sizes, key=get_aspect_ratio_difference)
            logger.info(f'選択したターゲットサイズ: {target_size}')
            
            # 画像をリサイズ
            img = img.resize(target_size, Image.LANCZOS)
            logger.info(f'画像をリサイズ: {img.size}')
            
            # 処理した画像をバイトストリームに変換
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            # Stability AI APIの認証ヘッダー
            headers = {
                "Authorization": f"Bearer {STABILITY_API_KEY}",
                "Accept": "application/json"
            }
            
            # Image-to-Imageエンドポイント
            endpoint = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/image-to-image"
            
            # プロンプトを生成
            generation_prompt, negative_prompt = generate_style_prompt(style)
            logger.info(f'生成プロンプト: {generation_prompt}')
            logger.info(f'ネガティブプロンプト: {negative_prompt}')
            
            # multipart/form-dataとして送信するファイル
            files = {
                "init_image": ("image.png", img_byte_arr, "image/png")
            }
            
            # パラメータの設定
            data = {
                "text_prompts[0][text]": generation_prompt,
                "text_prompts[0][weight]": "1.0",
                "text_prompts[1][text]": negative_prompt,
                "text_prompts[1][weight]": "-1.2",
                "image_strength": "0.4",    # 元の画像の影響を少し強める
                "cfg_scale": "9",          # プロンプトへの忠実度を上げる
                "samples": "1",
                "steps": "50",              # APIの制限に合わせる
                "style_preset": "photographic",
                "seed": str(random.randint(1, 1000000))
            }
            
            # APIリクエスト
            response = requests.post(endpoint, headers=headers, files=files, data=data)
            
            if response.status_code != 200:
                logger.error(f"Stability AI APIエラー: {response.text}")
                return jsonify({'error': f'画像生成に失敗しました: {response.text}'}), 500
            
            # レスポンスから画像データを取得
            response_data = response.json()
            if "artifacts" not in response_data or len(response_data["artifacts"]) == 0:
                return jsonify({'error': 'APIレスポンスに画像データが含まれていません'}), 500
            
            image_base64 = response_data["artifacts"][0]["base64"]
            image_bytes = base64.b64decode(image_base64)
            
            # 生成された画像を保存
            result_filename = f'styled-{timestamp}.png'
            result_path = os.path.join(images_dir, result_filename)
            
            with open(result_path, 'wb') as f:
                f.write(image_bytes)
            
            logger.info('生成された画像を保存: %s', result_path)
            
            # レスポンスを返す
            return jsonify({
                'imageUrl': f'/generated-images/{result_filename}',
                'originalUrl': f'/generated-images/{original_filename}',
                'message': '部屋のスタイル変更が完了しました'
            })
            
        except Exception as api_error:
            logger.error('Stability AI APIエラー: %s', str(api_error), exc_info=True)
            return jsonify({'error': f'画像生成に失敗しました: {str(api_error)}'}), 500
            
    except Exception as error:
        logger.error('部屋のスタイル変更エラー: %s', str(error), exc_info=True)
        return jsonify({'error': f'部屋のスタイル変更に失敗しました: {str(error)}'}), 500

@app.route('/api/transform-room-area', methods=['POST'])
def transform_room_area():
    """
    アプローチB: 部屋の特定の領域を変更
    """
    try:
        data = request.json
        image_data = data.get('imageData')
        mask_data = data.get('maskData')
        prompt = data.get('prompt')
        
        if not image_data:
            return jsonify({'error': '画像データが必要です'}), 400
        
        if not mask_data:
            return jsonify({'error': 'マスクデータが必要です'}), 400
        
        if not prompt:
            return jsonify({'error': 'プロンプトが必要です'}), 400
        
        logger.info('部屋の領域変更リクエスト受信')
        logger.info('プロンプト: %s', prompt)
        
        # プロンプトを英語に翻訳
        translated_prompt = translate_text(prompt)
        logger.info('翻訳されたプロンプト: %s', translated_prompt)
        
        # Base64データからPIL Imageに変換
        try:
            # Base64のヘッダー部分を削除
            base64_image = image_data.split(',')[1] if ',' in image_data else image_data
            image_bytes = base64.b64decode(base64_image)
            
            base64_mask = mask_data.split(',')[1] if ',' in mask_data else mask_data
            mask_bytes = base64.b64decode(base64_mask)
            
            # 画像を保存
            timestamp = int(time.time())
            original_filename = f'original-{timestamp}.png'
            original_path = os.path.join(images_dir, original_filename)
            
            with open(original_path, 'wb') as f:
                f.write(image_bytes)
            
            logger.info('元の画像を保存: %s', original_path)
            local_original_url = f'/generated-images/{original_filename}'
            
            # マスク画像を保存
            mask_filename = f'mask-{timestamp}.png'
            mask_path = os.path.join(images_dir, mask_filename)
            
            with open(mask_path, 'wb') as f:
                f.write(mask_bytes)
            
            logger.info('マスク画像を保存: %s', mask_path)
            
            # 画像を前処理
            try:
                # PILを使用して画像を開く前にデバッグ情報を出力
                logger.info('画像バイト数: %d', len(image_bytes))
                logger.info('マスクバイト数: %d', len(mask_bytes))
                
                # 画像フォーマットを明示的に指定してオープン
                img = Image.open(io.BytesIO(image_bytes))
                img = img.convert("RGB")
                
                # マスク画像も同様に処理
                try:
                    mask_img = Image.open(io.BytesIO(mask_bytes))
                    mask_img = mask_img.convert("RGB")
                except Exception as mask_error:
                    logger.error("マスク画像処理エラー: %s", str(mask_error))
                    
                    # マスク画像が読み込めない場合、単純な黒い画像を作成
                    mask_img = Image.new("RGB", img.size, (0, 0, 0))
                    # 中央に白い円を描画（サンプルマスク）
                    from PIL import ImageDraw
                    draw = ImageDraw.Draw(mask_img)
                    center_x, center_y = img.width // 2, img.height // 2
                    radius = min(img.width, img.height) // 4
                    draw.ellipse((center_x - radius, center_y - radius, 
                                  center_x + radius, center_y + radius), fill=(255, 255, 255))
                
                # 画像のサイズを取得
                width, height = img.size
                
                # 正方形に変換（APIが正方形の画像を期待する場合）
                square_size = max(width, height)
                square_img = Image.new("RGB", (square_size, square_size), (255, 255, 255))  # 白背景
                square_mask = Image.new("L", (square_size, square_size), 0)  # 黒（マスクなし）
                
                # 元の画像を中央に配置
                paste_x = (square_size - width) // 2
                paste_y = (square_size - height) // 2
                square_img.paste(img, (paste_x, paste_y))
                square_mask.paste(mask_img, (paste_x, paste_y))
                
                # 処理用に1024x1024にリサイズ
                api_img = square_img.resize((1024, 1024), Image.LANCZOS)
                api_mask = square_mask.resize((1024, 1024), Image.LANCZOS)
                
                # 処理した画像を保存
                processed_filename = f'processed-{timestamp}.png'
                processed_path = os.path.join(images_dir, processed_filename)
                api_img.save(processed_path, format="PNG", quality=95)
                
                processed_mask_filename = f'processed-mask-{timestamp}.png'
                processed_mask_path = os.path.join(images_dir, processed_mask_filename)
                api_mask.save(processed_mask_path, format="PNG", quality=95)
                
                logger.info('前処理した画像を保存: %s', processed_path)
                logger.info('前処理したマスクを保存: %s', processed_mask_path)
                
            except Exception as img_error:
                logger.error("画像処理エラー: %s", str(img_error))
                return jsonify({'error': f'画像処理に失敗しました: {str(img_error)}'}), 500
            
            try:
                # Stability AI APIの認証ヘッダー
                headers = {
                    "Authorization": f"Bearer {STABILITY_API_KEY}",
                    "Accept": "application/json"
                }
                
                # Inpaintingエンドポイント
                endpoint = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/image-to-image/masking"
                
                # プロンプトを強化
                generation_prompt = f"""
                Change ONLY the masked area to: {translated_prompt}
                
                The masked area should be completely transformed according to the prompt.
                Keep everything else EXACTLY the same. Maintain the same perspective, lighting, and overall style.
                Photorealistic, professional interior photography, detailed textures, natural lighting, 8K quality
                """
                
                negative_prompt = "deformed, distorted, disfigured, poorly drawn, bad anatomy, wrong proportions, blurry, bad hands, cropped, worst quality, low quality, jpeg artifacts, watermark, unnatural lighting, unrealistic, artificial, fake looking, cartoon, anime, illustration, painting, drawing, art, canvas texture, smooth texture, grainy, low-res, pixelated, oversaturated"
                
                # multipart/form-dataとして送信
                files = {
                    "init_image": open(processed_path, "rb"),
                    "mask_image": open(processed_mask_path, "rb")
                }
                
                # パラメータの設定
                data = {
                    "text_prompts[0][text]": generation_prompt,
                    "text_prompts[0][weight]": "1.0",
                    "text_prompts[1][text]": negative_prompt,
                    "text_prompts[1][weight]": "-1.0",
                    "mask_source": "MASK_IMAGE_WHITE",  # 白い部分がマスク（変更する部分）
                    "cfg_scale": "10",        # プロンプトへの忠実度を上げる
                    "samples": "1",
                    "steps": "50",            # ステップ数を増やす
                    "style_preset": "photographic",  # 写真風のスタイル
                    "seed": str(random.randint(1, 1000000))  # ランダムシード
                }
                
                # APIリクエスト
                response = requests.post(endpoint, headers=headers, files=files, data=data)
                
                if response.status_code != 200:
                    logger.error(f"Stability AI APIエラー: {response.text}")
                    return jsonify({'error': f'画像生成に失敗しました: {response.text}'}), 500
                
                # レスポンスから画像データを取得
                response_data = response.json()
                if "artifacts" not in response_data or len(response_data["artifacts"]) == 0:
                    return jsonify({'error': 'APIレスポンスに画像データが含まれていません'}), 500
                
                image_base64 = response_data["artifacts"][0]["base64"]
                image_bytes = base64.b64decode(image_base64)
                
                # 生成された画像を元のサイズに戻す処理
                generated_img = Image.open(io.BytesIO(image_bytes))
                
                # 正方形から元のアスペクト比に戻す
                generated_square = generated_img.resize((square_size, square_size), Image.LANCZOS)
                
                # 元のサイズの画像を切り出す
                final_img = generated_square.crop((paste_x, paste_y, paste_x + width, paste_y + height))
                
                # 最終画像を保存
                result_filename = f'masked-{timestamp}.png'
                result_path = os.path.join(images_dir, result_filename)
                
                # BytesIOを使用してメモリ内で処理
                final_bytes = io.BytesIO()
                final_img.save(final_bytes, format="PNG", quality=95)
                final_bytes.seek(0)
                
                with open(result_path, 'wb') as f:
                    f.write(final_bytes.read())
                
                logger.info('生成された画像を保存: %s', result_path)
                
                # レスポンスを返す
                local_image_url = f'/generated-images/{result_filename}'
                return jsonify({
                    'imageUrl': local_image_url,
                    'originalUrl': local_original_url,
                    'message': '部屋の領域変更が完了しました'
                })
                
            except Exception as api_error:
                logger.error('Stability AI APIエラー: %s', str(api_error), exc_info=True)
                return jsonify({'error': f'画像生成に失敗しました: {str(api_error)}'}), 500
        
        except Exception as error:
            logger.error('部屋の領域変更エラー: %s', str(error), exc_info=True)
            return jsonify({'error': f'部屋の領域変更に失敗しました: {str(error)}'}), 500
    
    except Exception as error:
        logger.error('部屋の領域変更エラー: %s', str(error), exc_info=True)
        return jsonify({'error': f'部屋の領域変更に失敗しました: {str(error)}'}), 500

@app.route('/api/customize-room', methods=['POST'])
def customize_room():
    try:
        data = request.json
        image_data = data.get('imageData')
        prompt = data.get('prompt')
        
        if not image_data:
            return jsonify({'error': '画像データが必要です'}), 400
        
        if not prompt or not prompt.strip():
            return jsonify({'error': 'プロンプトが必要です'}), 400
        
        logger.info('部屋のカスタマイズリクエスト受信')
        logger.info('プロンプト: %s', prompt)
        
        # プロンプトを英語に翻訳
        translated_prompt = translate_text(prompt)
        logger.info('翻訳されたプロンプト: %s', translated_prompt)
        
        # プロンプトを解析して具体的な変更指示を生成
        change_request = parse_room_change_request(prompt)
        specific_prompt = generate_specific_prompt(change_request)
        logger.info('生成された具体的なプロンプト: %s', specific_prompt)
        
        # Base64データを取得
        base64_data = image_data.split(',')[1] if ',' in image_data else image_data
        image_bytes = base64.b64decode(base64_data)
        
        # 画像を保存
        timestamp = int(time.time())
        original_filename = f'original-{timestamp}.png'
        original_path = os.path.join(images_dir, original_filename)
        
        with open(original_path, 'wb') as f:
            f.write(image_bytes)
        
        logger.info('元の画像を保存: %s', original_path)
        local_original_url = f'/generated-images/{original_filename}'
        
        # 画像を前処理（リサイズと最適化）
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img = img.convert("RGB")
            
            # アスペクト比を保持しながら、許可されているサイズに変換
            original_aspect_ratio = img.width / img.height
            
            # 許可されているサイズのリスト
            allowed_sizes = [
                (1024, 1024),
                (1152, 896),
                (1216, 832),
                (1344, 768),
                (1536, 640),
                (640, 1536),
                (768, 1344),
                (832, 1216),
                (896, 1152)
            ]
            
            # 最適なサイズを選択
            def get_aspect_ratio_difference(size):
                return abs((size[0] / size[1]) - original_aspect_ratio)
            
            target_size = min(allowed_sizes, key=get_aspect_ratio_difference)
            logger.info(f'選択したターゲットサイズ: {target_size}')
            
            # 画像をリサイズ
            img = img.resize(target_size, Image.LANCZOS)
            logger.info(f'画像をリサイズ: {img.size}')
            
            processed_filename = f'processed-{timestamp}.png'
            processed_path = os.path.join(images_dir, processed_filename)
            img.save(processed_path, format="PNG", quality=95)
            logger.info('前処理した画像を保存: %s', processed_path)
        except Exception as img_error:
            logger.error("画像処理エラー: %s", str(img_error))
            return jsonify({'error': f'画像処理に失敗しました: {str(img_error)}'}), 500
        
        try:
            # Stability AI APIの認証ヘッダー
            headers = {
                "Authorization": f"Bearer {STABILITY_API_KEY}",
                "Accept": "application/json"
            }
            
            # 最新のStability AI APIエンドポイント
            endpoint = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/image-to-image"
            
            # プロンプトを作成（より強力な指示）
            generation_prompt = f"""
            THIS IS AN IMAGE-TO-IMAGE TASK.
            
            SPECIFIC INSTRUCTION: {specific_prompt}
            
            DO NOT change the room layout, perspective, or camera angle.
            DO NOT add or remove furniture unless explicitly requested.
            ONLY modify the exact elements mentioned in the instruction.
            
            Photorealistic, professional interior photography, detailed textures, natural lighting
            """
            
            negative_prompt = "deformed, distorted, disfigured, poorly drawn, bad anatomy, wrong proportions, blurry, bad hands, cropped, worst quality, low quality, jpeg artifacts, watermark, unnatural lighting, unrealistic, artificial, fake looking, cartoon, anime, illustration, painting, drawing, art, canvas texture, smooth texture, grainy, low-res, pixelated, oversaturated, different layout, different furniture, different room, different perspective"
            
            # multipart/form-dataとして送信
            files = {
                "init_image": open(processed_path, "rb")
            }
            
            # 重要なパラメータの調整
            data = {
                "text_prompts[0][text]": generation_prompt,
                "text_prompts[0][weight]": "1.0",
                "text_prompts[1][text]": negative_prompt,
                "text_prompts[1][weight]": "-1.0",
                "image_strength": "0.5",  # 元の画像の影響を35%に設定（変更をより反映）
                "cfg_scale": "10",        # プロンプトへの忠実度を最大限に
                "samples": "1",
                "steps": "50",            # ステップ数を増やして品質向上
                "style_preset": "photographic",  # 写真風のスタイル
                "seed": str(random.randint(1, 1000000))  # ランダムシード
            }
            
            # APIリクエスト
            response = requests.post(endpoint, headers=headers, files=files, data=data)
            
            if response.status_code != 200:
                logger.error(f"Stability AI APIエラー: {response.text}")
                return jsonify({'error': f'画像生成に失敗しました: {response.text}'}), 500
            
            # レスポンスから画像データを取得
            response_data = response.json()
            if "artifacts" not in response_data or len(response_data["artifacts"]) == 0:
                return jsonify({'error': 'APIレスポンスに画像データが含まれていません'}), 500
            
            image_base64 = response_data["artifacts"][0]["base64"]
            image_bytes = base64.b64decode(image_base64)
            
            # 画像を保存
            result_filename = f'edited-{timestamp}.png'
            result_path = os.path.join(images_dir, result_filename)
            
            with open(result_path, 'wb') as f:
                f.write(image_bytes)
            
            logger.info('生成された画像を保存: %s', result_path)
            
            # レスポンスを返す
            local_image_url = f'/generated-images/{result_filename}'
            return jsonify({
                'imageUrl': local_image_url,
                'originalUrl': local_original_url,
                'message': '部屋のカスタマイズが完了しました'
            })
            
        except Exception as api_error:
            logger.error('Stability AI APIエラー: %s', str(api_error), exc_info=True)
            return jsonify({'error': f'画像生成に失敗しました: {str(api_error)}'}), 500
    
    except Exception as error:
        logger.error('部屋のカスタマイズエラー: %s', str(error), exc_info=True)
        return jsonify({'error': f'部屋のカスタマイズに失敗しました: {str(error)}'}), 500

def generate_specific_prompt(change_request):
    """
    解析された変更リクエストから具体的なプロンプトを生成
    """
    if not change_request:
        return "Make the room look better while keeping the same layout and furniture."
    
    part = change_request.get("part")
    color = change_request.get("color")
    
    if not part and not color:
        return "Make the room look better while keeping the same layout and furniture."
    
    # より強力なプロンプトを生成
    prompt_parts = []
    
    if part and color:
        if part == "floor":
            return f"Change ONLY the floor to {color} color. The floor should be {color}. Keep everything else exactly the same."
        elif part == "wall":
            return f"Change ONLY the walls to {color} color. The walls should be {color}. Keep everything else exactly the same."
        elif part == "ceiling":
            return f"Change ONLY the ceiling to {color} color. The ceiling should be {color}. Keep everything else exactly the same."
        elif part == "furniture":
            return f"Change ONLY the furniture to {color} color. The furniture should be {color}. Keep everything else exactly the same."
        elif part == "curtains":
            return f"Change ONLY the curtains to {color} color. The curtains should be {color}. Keep everything else exactly the same."
        elif part == "lighting":
            return f"Change ONLY the lighting to {color} tone. The lighting should be {color}. Keep everything else exactly the same."
    elif part:
        if part == "floor":
            return f"Change ONLY the floor. Keep everything else exactly the same."
        elif part == "wall":
            return f"Change ONLY the walls. Keep everything else exactly the same."
        elif part == "ceiling":
            return f"Change ONLY the ceiling. Keep everything else exactly the same."
        elif part == "furniture":
            return f"Change ONLY the furniture. Keep everything else exactly the same."
        elif part == "curtains":
            return f"Change ONLY the curtains. Keep everything else exactly the same."
        elif part == "lighting":
            return f"Change ONLY the lighting. Keep everything else exactly the same."
    elif color:
        return f"Change the color scheme to {color}. The room should have {color} tones."
    
    return "Make the room look better while keeping the same layout and furniture."

# プロンプト生成部分を修正
def generate_style_prompt(style):
    style_info = STYLE_DETAILS.get(style, STYLE_DETAILS["simple"])
    
    main_prompt = f"""
    Transform this interior space into a {style_info['main']}.
    
    Style requirements:
    - Colors: {style_info['colors']}
    - Materials: {style_info['materials']}
    - Furniture: {style_info['furniture']}
    - Lighting: {style_info['lighting']}
    - Atmosphere: {style_info['mood']}
    
    Critical requirements:
    - Maintain the exact room layout and dimensions
    - Keep all window and door positions unchanged
    - Preserve the room's basic structure
    - Create photorealistic interior photography quality
    - Ensure perfect perspective and spatial coherence
    - Use appropriate lighting and shadows
    - Generate in ultra-high-definition 8K quality
    - Create realistic materials and textures
    
    This must be a photorealistic interior design visualization, not an artistic interpretation.
    ((highly detailed)), ((ultra realistic)), ((photorealistic)), ((interior design)), ((professional photography))
    """

    negative_prompt = """
    ((deformed)), ((distorted)), ((disfigured)), ((poorly drawn)), ((bad anatomy)), ((wrong proportions)),
    ((blurry)), ((pixelated)), ((grainy)), ((low quality)), ((jpeg artifacts)), ((compression artifacts)),
    ((watermark)), ((signature)), ((text)), ((logo)),
    ((unrealistic lighting)), ((bad shadows)), ((harsh lighting)), ((overexposed)), ((underexposed)),
    ((cartoon)), ((anime)), ((illustration)), ((painting)), ((3d render)), ((cgi)), ((artificial)),
    ((oversaturated)), ((unrealistic colors)), ((color bleeding)),
    ((out of frame)), ((cropped)), ((cut off)),
    ((wrong perspective)), ((distorted space)), ((curved lines)), ((warped surfaces)),
    ((duplicate)), ((multiple)), ((repeating elements))
    """

    return main_prompt, negative_prompt

if __name__ == '__main__':
    # Renderのポート設定を取得（デフォルトは5000）
    port = int(os.environ.get('PORT', 5000))
    
    # 本番環境（Render）かローカル環境かを判定
    if os.environ.get('RENDER'):
        # Render環境での起動設定
        app.run(host='0.0.0.0', port=port)
    else:
        # ローカル環境での起動設定
        app.run(host='localhost', port=port, debug=True)