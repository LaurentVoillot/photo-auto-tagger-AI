# Photo Auto Tagger

🏷️ **Automatic photo tagging for Adobe Lightroom Classic using local AI vision models**

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## ✨ Features

- 🤖 **Local AI tagging** using Ollama vision models (Qwen2-VL, LLaVA, MiniCPM-V, etc.)
- 🖼️ **Smart Previews support** - Process photos without mounting external drives
- ⏸️ **Pause/Resume** - Handle large catalogs (200,000+ photos) across multiple sessions
- 🌍 **Multi-language tags** - Generate tags in French, English, Spanish, German, etc.
- 📊 **Real-time progress** - Live statistics with 3 indicators (Progress %, Tagged, Total)
- 💾 **Dual output** - Write tags to both Lightroom catalog AND XMP sidecar files
- 🏷️ **Custom suffix** - Distinguish AI tags from manual tags (e.g., `_ai` suffix)
- 💿 **Multi-disk support** - Intelligent caching for photos across multiple drives
- 🔒 **Privacy-first** - 100% local processing, no cloud uploads

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **Adobe Lightroom Classic** (tested with v13-15)
- **Ollama** ([install here](https://ollama.com))

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/photo-auto-tagger.git
cd photo-auto-tagger

# Install dependencies
pip install -r requirements.txt

# Install a vision model
ollama pull qwen2-vl
```

### Usage

```bash
# Launch the GUI
python3 photo_tagger_gui.py
```

**Steps:**
1. Select your Lightroom catalog (`.lrcat` file)
2. Choose an Ollama vision model
3. Configure tag language (French, English, etc.)
4. Enable/disable AI tag suffix (`_ai`)
5. Click **START** to begin tagging

## 📖 Documentation

### Tag Language Configuration

Edit `config.py`:

```python
# Set tag language
TAG_LANGUAGE = "english"  # or "français", "español", "deutsch", etc.
```

### Smart Previews

For best performance without external drives:

1. In Lightroom: Select photos → `Library > Previews > Build Smart Previews`
2. The app will automatically use Smart Previews (10-100x faster than original files)

### Pause & Resume

- Click **PAUSE** at any time
- Close the application
- Restart later and click **START** - it will resume from where you left off

### Multi-language Support

The app generates tags in the language specified in `config.TAG_LANGUAGE`:

- **French**: `Montagne, Lac, Paysage, Neige`
- **English**: `Mountain, Lake, Landscape, Snow`
- **Spanish**: `Montaña, Lago, Paisaje, Nieve`

## 🏗️ Architecture

```
Adobe_images → AgLibraryFile → AgDNGProxyInfo
  (photo)      (file info)      (Smart Preview UUID)
                                      ↓
                            X/XXXX/UUID.dng
                       (Smart Preview DNG file)
```

### Key Components

- **`photo_tagger_gui.py`** - Main GUI application
- **`lightroom_manager.py`** - Lightroom catalog & Smart Previews handling
- **`ollama_client.py`** - Ollama API integration
- **`xmp_manager.py`** - XMP sidecar file management
- **`config.py`** - User-configurable settings

## 🔧 Advanced Configuration

### LLM Optimization for Your Hardware

**Performance depends heavily on your system configuration!** Optimize Ollama for your hardware:

#### 🖥️ Hardware Requirements

| Component | Minimum | Recommended | Optimal |
|-----------|---------|-------------|---------|
| **RAM** | 16 GB | 32 GB | 64 GB+ |
| **GPU VRAM** | 6 GB | 8 GB | 12 GB+ |
| **CPU** | 4 cores | 8 cores | 16 cores+ |
| **Storage** | HDD | SSD | NVMe SSD |

#### ⚡ Model Selection by Hardware

Choose the right model for your system:

```bash
# For systems with 32GB+ RAM and good GPU (RTX 3060+)
ollama pull qwen2-vl:7b       # Best quality/speed balance

# For systems with 16-32GB RAM
ollama pull qwen2-vl:3b       # Lighter, faster

# For older/limited hardware
ollama pull llava:7b          # More compatible
```

#### 🎯 Creating Custom Optimized Models

**Example**: Create a faster variant optimized for your hardware

```bash
# Create a Modelfile
cat > qwen-fast << EOF
FROM qwen2-vl:7b

# Optimize for speed over creativity
PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER num_ctx 2048
PARAMETER num_predict 100

# System prompt for concise tagging
SYSTEM You are a photo tagging expert. Generate precise, concise keywords only.
EOF

# Build the custom model
ollama create qwen-fast -f qwen-fast

# Use it in the app
# Select "qwen-fast" in the model dropdown
```

#### 🚀 Performance Tips

1. **Use Smart Previews** (10-100x faster)
   ```
   Lightroom → Select All → Library → Previews → Build Smart Previews
   ```

2. **Adjust image size** in `config.py`:
   ```python
   IMAGE_MAX_SIZE = 1024  # Lower = faster (512, 768, 1024, 2048)
   JPEG_QUALITY = 70      # Lower = faster (50-90)
   ```

3. **GPU acceleration** (if available):
   ```bash
   # Check GPU usage
   nvidia-smi  # NVIDIA
   rocm-smi    # AMD
   
   # Ollama uses GPU automatically if detected
   ```

4. **Concurrent processing**:
   ```python
   # In config.py (future feature)
   PARALLEL_WORKERS = 2  # Process 2 photos simultaneously
   ```

#### 📊 Expected Performance

With **32GB RAM** + **RTX 3060** + **qwen2-vl:7b** + **Smart Previews**:

| Catalog Size | Processing Time | Speed |
|--------------|-----------------|-------|
| 1,000 photos | ~15 minutes | ~4 photos/min |
| 10,000 photos | ~2.5 hours | ~66 photos/min |
| 100,000 photos | ~1 day | ~70 photos/min |
| 214,129 photos | ~2 days | ~75 photos/min |

**Without Smart Previews**: 5-10x slower (especially on external drives)

#### 🔍 Monitoring Performance

```bash
# Terminal 1: Monitor Ollama
ollama logs

# Terminal 2: Monitor system resources
# macOS
top -o cpu

# Linux
htop

# Check if GPU is being used
nvidia-smi -l 1  # Update every second
```

#### 💡 Troubleshooting Slow Performance

**Problem**: Tags taking 10+ seconds per photo

**Solutions**:
1. ✅ Create Smart Previews in Lightroom
2. ✅ Use a smaller/faster model (`qwen2-vl:3b` instead of `7b`)
3. ✅ Reduce `IMAGE_MAX_SIZE` to 512 or 768
4. ✅ Close other applications
5. ✅ Check if GPU is detected: `ollama run qwen2-vl "test"`
6. ✅ Upgrade RAM if constantly swapping

#### 📈 Benchmark Your System

```bash
# Quick benchmark
python3 test_installation.py

# This will test:
# - Ollama connection
# - Model loading speed
# - Inference speed
# - Smart Preview detection
```

---

### Configuration File

Edit `config.py` for advanced options:

```python
# Model parameters
OLLAMA_TIMEOUT = 300           # Request timeout (seconds)
TEMPERATURE = 0.1              # Lower = more deterministic tags
MAX_TOKENS = 100               # Max tokens per response

# Image processing
IMAGE_MAX_SIZE = 1024          # Max image dimension (pixels)
JPEG_QUALITY = 70              # JPEG compression quality

# Tags
TAG_SUFFIX = "_ai"             # Suffix for AI-generated tags
TAG_SUFFIX_ENABLED = True      # Enable/disable suffix
MAX_TAGS_PER_PHOTO = 15        # Max tags per photo

# Logging
LOG_LEVEL = "INFO"             # DEBUG, INFO, WARNING, ERROR
```

## 📊 Performance

Tested on **214,129 photos** with **210,460 Smart Previews** (98.3% coverage):

- **With Smart Previews**: ~0.1-0.5 sec/photo
- **Without Smart Previews**: ~2-10 sec/photo
- **Recommended**: Create Smart Previews for optimal performance

## 🐛 Troubleshooting

### "No Smart Preview available"

**Solution**: Create Smart Previews in Lightroom or mount external drives.

### "Ollama connection error"

**Solution**: 
```bash
# Check if Ollama is running
ollama list

# Start Ollama if needed
ollama serve
```

### Smart Previews not found

**Diagnostic**:
```bash
python3 diagnose_smart_previews_structure.py /path/to/catalog.lrcat
```

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the **GNU General Public License v3.0 or later** - see the [LICENSE](LICENSE) file for details.

### Third-Party Licenses

- **Pillow**: [HPND License](https://github.com/python-pillow/Pillow/blob/main/LICENSE)
- **Requests**: [Apache 2.0](https://github.com/psf/requests/blob/main/LICENSE)
- **python-xmp-toolkit**: [BSD-3-Clause](https://github.com/python-xmp-toolkit/python-xmp-toolkit/blob/master/LICENSE)

All dependencies are compatible with GPL-3.0+.

## 🙏 Acknowledgments

- **Ollama** - Local LLM inference engine
- **Qwen2-VL** - Vision-language model by Alibaba Cloud
- **Adobe Lightroom** - Professional photo management software

## 📧 Contact

- **Issues**: [GitHub Issues](https://github.com/yourusername/photo-auto-tagger/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/photo-auto-tagger/discussions)

---

Made with ❤️ for photographers who value privacy and local processing
