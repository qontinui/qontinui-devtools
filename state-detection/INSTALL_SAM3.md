# SAM3 Installation Guide

## Prerequisites
- Python 3.12+
- PyTorch 2.7+ with CUDA 12.6+ (for GPU support)
- Hugging Face account with SAM3 access approved

## Installation Steps

### 1. Request Hugging Face Access
1. Visit https://huggingface.co/facebook/sam3
2. Click "Request Access" and fill out the form
3. Wait for approval email from Meta/Hugging Face

### 2. Install Dependencies

```bash
# Install PyTorch 2.7+ with CUDA 12.6+ (for GPU)
pip install torch==2.7.0 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126

# For CPU-only (slower, not recommended for production)
# pip install torch==2.7.0 torchvision torchaudio

# Install Hugging Face Hub
pip install huggingface_hub

# Install SAM3
pip install git+https://github.com/facebookresearch/sam3.git
```

### 3. Authenticate with Hugging Face

```bash
# Install Hugging Face CLI
pip install huggingface_hub[cli]

# Login (you'll need your Hugging Face token)
huggingface-cli login
```

**To get your token:**
1. Go to https://huggingface.co/settings/tokens
2. Click "New token"
3. Give it a name (e.g., "SAM3 Access")
4. Select "Read" permission
5. Copy the token
6. Paste it when prompted by `huggingface-cli login`

### 4. Download SAM3 Model (Automatic on First Use)

The SAM3 model will automatically download when you first run the application. The checkpoint will be saved to:
- `~/.cache/huggingface/hub/models--facebook--sam3-hiera-large/`

You can also manually download it:

```python
from sam3.build_sam import build_sam3_image_model

# This will download the checkpoint automatically
model = build_sam3_image_model()
```

### 5. Verify Installation

```bash
# Navigate to your project
cd /Users/jspinak/Documents/qontinui/qontinui-api

# Start the API server
uvicorn semantic_api:app --reload

# Check the health endpoint
curl http://localhost:8000/api/semantic/health
```

Expected response should show:
```json
{
  "status": "healthy",
  "qontinui_available": true,
  "clip_available": true,
  "sam3_available": true  // ← This should be true
}
```

## Troubleshooting

### Issue: SAM3 checkpoint not found
**Solution:** Ensure you've been approved for access and are authenticated:
```bash
huggingface-cli whoami  # Verify you're logged in
huggingface-cli download facebook/sam3  # Manually download
```

### Issue: CUDA not available
**Solution:** Install CUDA-enabled PyTorch:
```bash
pip install torch==2.7.0 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
```

### Issue: Out of memory
**Solution:**
- Close other applications
- Use a smaller batch size
- Consider using a GPU instance (AWS, etc.)

### Issue: Import errors
**Solution:** Ensure all dependencies are installed:
```bash
pip install torch torchvision torchaudio huggingface_hub
pip install git+https://github.com/facebookresearch/sam3.git
```

## Expected Model Size
- SAM3 model: ~3.5 GB
- Model parameters: 848 million
- GPU memory required: 8+ GB recommended

## Performance Expectations

| Hardware | Speed per Image | Recommendation |
|----------|----------------|----------------|
| CPU (Intel i5) | 30-60 seconds | Development only |
| GPU (RTX 2060) | 1-3 seconds | Good for development |
| GPU (RTX 3090) | 100-300ms | Production ready |
| GPU (A100) | 30-100ms | High performance |

## Next Steps

After installation:
1. Start the API: `uvicorn semantic_api:app --reload`
2. Start the frontend: `cd frontend && npm run dev`
3. Upload a screenshot
4. Select "SAM3" strategy
5. Enter a text prompt (e.g., "button")
6. Click "Process Image"

## Support

If you encounter issues:
1. Check the API logs for error messages
2. Verify SAM3 availability at `/api/semantic/health`
3. Ensure you have the latest code updates
4. Check GitHub issues: https://github.com/facebookresearch/sam3/issues
