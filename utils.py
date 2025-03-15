import os
from openai import OpenAI
from docx import Document
import json
import requests
import base64
import numpy as np
from io import BytesIO
from PIL import Image,ImageFont,ImageDraw
import wget
import time
from scenedetect import detect, ContentDetector,save_images,open_video


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME")

persist_directory='text_persist'
collection_name='text_collection'

# model_name="gpt-4o-mini-2024-07-18"
# model_name='o1-mini-2024-09-12'

client = OpenAI(api_key=OPENAI_API_KEY,base_url=OPENAI_BASE_URL)

def load_file(file_path):
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    docs = "\n".join(full_text)
    docs=docs[:40000]
    return docs

def response_generator(prompt=''):
    stream = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": 'user', "content": prompt}
        ],
        stream=True
    )
    return stream

def call_multi_model_gpt(prompt,images,image_mode='url'):
    content = [{"type": "text", "text": prompt}]
    for image in images:
        if image_mode=='url':
            image_url=image
        elif image_mode=='base64':
            image_url=f"data:image/jpeg;base64,{image}"
        elif image_mode=='local_path':
            base64_image=encode_image(image)
            image_url=f"data:image/jpeg;base64,{base64_image}"
        else:
            image_url=""
        content.append({"type": "image_url", "image_url": image_url})
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": content
            },
        ],
    )
    try:
        res=completion.choices[0].message.content
    except:
        res=""
    return res


def call_gpt_image_gen(prompt):
    response = client.images.generate(
        model="dall-e-3",
        prompt = prompt,
        size = "1024x1024",
        quality="standard",
        n=1,
    )
    return response.data[0].url
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

def stream_data(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.04)

def encode_image_to_base64(image_file):
    if image_file is not None:
        # 将上传的文件内容转换为 Base64 编码
        base64_image = base64.b64encode(image_file.getvalue()).decode("utf-8")
        return base64_image
    return None

def call_gpt_text2audio_gen(text,speech_file_name):
    speech_folder_path='./tmp_audios'
    if not os.path.exists(speech_folder_path):
        os.makedirs(speech_folder_path)
    response = client.audio.speech.create(
        model='tts-1',
        voice='echo',
        input=text
    )
    audio_file_path=os.path.join(speech_folder_path,'{}.mp3'.format(speech_file_name))
    response.stream_to_file(audio_file_path)
    if os.path.exists(audio_file_path):
        return audio_file_path
    else:
        return None

def parse_json_response(response):
    raw_res=response
    if "```json" in raw_res and "```" in raw_res:
        res = raw_res.split("```json")[1].split("```")[0]
    else:
        res = raw_res
    res = res.replace('\n', '').replace(' ', '')
    res = json.loads(res, strict=False)
    return res

def url_to_np_array(image_url):
    try:
        # 发送 HTTP 请求下载图片
        response = requests.get(image_url)
        response.raise_for_status()  # 确保请求成功

        # 使用 BytesIO 将下载的图片数据转换为可读的文件对象
        image_data = BytesIO(response.content)

        # 使用 PIL 打开图片
        image = Image.open(image_data)

        # 将图片转换为 NumPy 数组
        np_array = np.array(image)

        return np_array
    except Exception as e:
        print(f"Error: {e}")
        return None

# 将图片下载到本地，并返回本地路径
def download_image(image_url,img_name=None):
    # 从 URL 中提取文件名
    if img_name:
        filename = img_name
    else:
        if '?' in image_url:
            image_url = image_url.split('?')[0]
        filename = image_url.split("/")[-1]
    local_path = os.path.join('tmp_images', filename)
    if not os.path.exists('tmp_images'):
        os.makedirs('tmp_images')
    try:
        # 下载图片
        if not os.path.exists(local_path):
            wget.download(image_url, local_path)
        return local_path
    except Exception as e:
        print(f"Error: {e}")
        try:
            cmd=f'wget {image_url} -O {local_path}'
            os.system(cmd)
            return local_path
        except Exception as e:
            return None

def compute_resolution(resolution,ratio):
    w_r,h_r=ratio.split(':')
    w_r=float(w_r)
    h_r=float(h_r)
    res=int(resolution[:-1])
    if w_r>=h_r:
        width = res
        height=res/w_r*h_r
    else:
        height=res
        width=res/h_r*w_r
    return width,height

def crop_and_resize_img(img_path,target_width,target_height):
    img=Image.open(img_path)
    # 获取原始图片的宽度和高度
    original_width, original_height = img.size

    # 计算目标长宽比
    target_ratio = target_width / target_height
    original_ratio = original_width / original_height

    # 根据长宽比决定裁剪方式
    if original_ratio > target_ratio:
        # 原始图片比目标更宽，需要裁剪宽度
        new_width = int(original_height * target_ratio)
        left = (original_width - new_width) // 2
        upper = 0
        right = left + new_width
        lower = original_height
    else:
        # 原始图片比目标更高，需要裁剪高度
        new_height = int(original_width / target_ratio)
        left = 0
        upper = (original_height - new_height) // 2
        right = original_width
        lower = upper + new_height

    # 裁剪图片
    cropped_img = img.crop((left, upper, right, lower))
    # 调整大小到目标分辨率
    resized_img = cropped_img.resize((int(target_width), int(target_height)))
    return resized_img

def split_subtitle(text,audio_duration):
    parts=[]
    part=''
    total_len=0
    for word in text:
        if word not in ["，",",",".","。","!","！","?","？",":","："]:
            part+=word
        else:
            parts.append([part,len(part)])
            total_len+=len(part)
            part=""

    # 计算每段文字的时长
    new_parts=[]
    for p in parts:
        duration=float(audio_duration*p[1])/total_len
        new_parts.append([p[0],p[1],duration])
    return new_parts

def render_text_on_image(text,font_path,image,line_font_num=12,max_line_num=3):
    width,height=image.size
    new_image=image.copy()
    font_size=int(float(width)*0.9/line_font_num)
    lines=[]
    line=""
    for w in text:
        line=line+w
        if len(line)>=line_font_num:
            lines.append(line)
            line=""
    if len(line):
        lines.append(line)

    draw=ImageDraw.Draw(new_image)
    font = ImageFont.truetype(font_path, font_size)
    line_height = font.getbbox("测试")[3]
    y_position = int(height) - line_height*3-10
    for line in lines:
        text_width = font.getbbox(line)[2]
        x_position = (width - text_width) // 2
        draw.text((x_position, y_position), line, font=font, fill="white")
        y_position += line_height

    return new_image

def send_video_generation_request(prompt,image_urls,duration,resolution,movement_amplitude,aspect_ratio):
    # 定义 API 的 URL 和请求头
    api_url = "https://api.vidu.cn/ent/v2/reference2video"
    headers = {
        "Authorization": "Token vda_2683281298413230_IaL6zdK5jpWCdOsrI4bILoo62ca9jMQ0",  # 替换为您的实际 API Key
        "Content-Type": "application/json"
    }

    # 定义请求的 JSON 数据
    data = {
        "model": "vidu2.0",
        "images": image_urls,
        "prompt": prompt,
        "duration": duration,
        "seed": "0",
        "aspect_ratio": aspect_ratio,
        "resolution": resolution,
        "movement_amplitude": movement_amplitude
    }
    response = requests.post(api_url, headers=headers, data=json.dumps(data))
    return response.json()

def check_video_gen_status(task_id):
    api_key='vda_2683281298413230_IaL6zdK5jpWCdOsrI4bILoo62ca9jMQ0'

    # 定义 API 的 URL 和请求头
    api_url = f"https://api.vidu.cn/ent/v2/tasks/{task_id}/creations"  # 替换 {your_id} 为实际的任务 ID
    headers = {
        "Authorization": f"Token {api_key}"  # 替换 {your_api_key} 为您的实际 API Key
    }

    # 发送 GET 请求
    response = requests.get(api_url, headers=headers)

    # 打印响应内容
    if response.status_code == 200:
        return response.json()['creations']
    else:
        return []

def upload_img_to_url(img_path=''):
    url = 'https://s1.a2k6.com/mrjtm007/api/upload/'
    api_token = '973115c87ee3753cf44e'
    files = {'uploadedFile': ('demo.jpg', open(img_path, 'rb'), "image/jpeg")}
    data = {'api_token': api_token,
            'upload_format': 'file',  # 可选值 file 、base64 或者 url，不填则默认为file
            'mode': '1',
            'watermark': '0',
            }
    res = requests.post(url, data=data, files=files)
    if res.status_code == 200:
        return res.json()['url']
    else:
        return ''

def get_key_frames(video_path):
    scene_folder_path = 'tmp_scenes'
    if not os.path.exists(scene_folder_path):
        os.makedirs(scene_folder_path)
    video_name = video_path.split('/')[-1].split('.')[0]
    video_folder_path = os.path.join(scene_folder_path, video_name)
    os.makedirs(video_folder_path, exist_ok=True)

    # 场景分割解析
    # min_scene_len=40,每个场景最少40帧
    # min_scene_len=
    scene_list = detect(video_path, ContentDetector(min_scene_len=40))

    # 保存切割结果
    # ffmpeg_arg = '-c:v libx264 -preset veryfast -crf 22 -c:a aac'
    # ffmpeg_arg = '-c:v copy -c:a copy'
    # split_video_ffmpeg(video_path, scene_list, video_name=video_name, show_progress=True, arg_override=ffmpeg_arg)
    video = open_video(video_path)
    save_images(scene_list, video, 1, output_dir=video_folder_path, show_progress=True)
    return video_folder_path