# Demo Text to Video

Thư mục này có thể copy riêng sang máy khác để cài và chạy.
Cần GPU NVIDIA với driver tương thích CUDA 13 và các gói hệ thống:

```bash
sudo apt-get update
sudo apt-get install -y git curl python3 python3-venv python3-pip ffmpeg
```

## Setup lần đầu

```bash
cd /home/shadeform/apps/test-i2v/text_to_video
bash setup.sh
```

Script tự cài ComfyUI, môi trường Python, dependency web, custom node và tải model.
Nếu đã có `../ComfyUI`, script dùng lại để tránh tải model lần nữa.
Khi copy riêng thư mục này, ComfyUI được cài ngay tại `./ComfyUI`.
Có thể đặt `COMFYUI_DIR=/duong/dan/ComfyUI` cho cả setup và run để dùng vị trí khác.

## Chạy demo

```bash
bash run.sh
```

Script mở ComfyUI, đợi sẵn sàng rồi chạy web tại http://localhost:8000.
Nếu ComfyUI đã chạy ở cổng 8188, script dùng lại.
Ctrl+C dừng các tiến trình do script mở; ComfyUI có sẵn vẫn chạy.
Có thể đặt `WEB_PORT`, `COMFY_PORT`, hoặc `COMFY_URL` để dùng cổng/ComfyUI khác.

Workflow: `workflow_text_only.json`.
Prompt → DetectNSFWText → MiniMaxH3SilentPrompt → MiniMax H3.
Mặc định 3 giây (48 frame, 16 FPS), seed ngẫu nhiên mỗi lần tạo.
Freepik kiểm tra video (level low, threshold 0.8, 3 frame ngẫu nhiên mỗi giây)
trước khi cho phát hoặc tải. Lần kiểm tra đầu tiên tự tải model Freepik.

## Docker

```bash
docker compose build
MODEL_ROOT="$PWD/models" bash download_models.sh
docker compose up -d
```

## Kiểm thử

```bash
../ComfyUI/.venv/bin/python -m unittest discover -s tests -v
```

Nếu cài ComfyUI ngay trong thư mục này, dùng `ComfyUI/.venv/bin/python`.
# test-t2v
