# 🔥 StoryForge AI Serverless

Geração automática de vídeos curtos com IA para RunPod Serverless.

---

## 📁 Arquivos

```
StoryForgeAI/
├── Dockerfile          # Build sem HEALTHCHECK (corrigido)
├── handler.py          # Handler completo com todas funcionalidades
└── requirements.txt    # Dependências (com gtts)
```

---

## 🚀 Deploy no RunPod

### 1. Criar Repositório no GitHub

Se ainda não existe, crie um repositório:
- Nome: `StoryForgeAI`
- Visibilidade: Public ou Private

### 2. Fazer Upload dos Arquivos

**Opção A: Via GitHub Web Interface**
1. Acesse: https://github.com/ymhp64t9bz-png/StoryForgeAI
2. Upload os 3 arquivos:
   - `Dockerfile`
   - `handler.py`
   - `requirements.txt`

**Opção B: Via Git (se for repositório local)**
```bash
cd "C:\Users\Alec Guimel\.gemini\antigravity\scratch\autoshorts-clone\deploy_cloud\StoryForgeAI"
git init
git add .
git commit -m "Initial commit: StoryForge AI Serverless"
git remote add origin https://github.com/ymhp64t9bz-png/StoryForgeAI.git
git push -u origin main
```

### 3. Configurar Endpoint no RunPod

1. **RunPod Console** → **Serverless** → **New Endpoint**
2. **Configurações:**
   - **Name:** StoryForgeAI
   - **Repository:** `https://github.com/ymhp64t9bz-png/StoryForgeAI.git`
   - **Branch:** `main`
   - **Dockerfile Path:** `Dockerfile`
   - **Container Disk:** 10 GB
   - **GPU:** RTX 3090 ou similar

3. **Environment Variables** (opcional):
   ```
   B2_KEY_ID=your_key_id
   B2_APP_KEY=your_app_key
   B2_BUCKET_NAME=your_bucket_name
   B2_ENDPOINT=https://s3.us-east-005.backblazeb2.com
   ```

4. **Deploy**

---

## 🧪 Testar

### Teste Básico
```json
{
  "input": {
    "mode": "test"
  }
}
```

**Resposta esperada:**
```json
{
  "status": "success",
  "message": "StoryForge AI worker funcionando!",
  "version": "2.0",
  "features": {
    "moviepy": true,
    "pil": true,
    "edge_tts": false,
    "gtts": true,
    "b2": true
  }
}
```

### Gerar Vídeo com Tópico
```json
{
  "input": {
    "topic": "Inteligência Artificial",
    "style": "viral",
    "duration": 60,
    "num_images": 3
  }
}
```

### Gerar Vídeo com Script Customizado
```json
{
  "input": {
    "script": "Olá! Este é meu script personalizado sobre tecnologia...",
    "title": "Tecnologia do Futuro",
    "style": "educational",
    "num_images": 5
  }
}
```

---

## 🎯 Funcionalidades

### ✅ Geração de Script
- 3 estilos: `viral`, `educational`, `story`
- Templates baseados no StoryForge local
- Inclui título, script, hashtags e CTA

### ✅ Geração de Áudio
- **gTTS** (Google Text-to-Speech)
- **Edge-TTS** (suporte futuro)
- Múltiplas vozes e idiomas

### ✅ Geração de Imagens
- Imagens placeholder coloridas
- Gradientes visuais
- Texto sobreposto

### ✅ Composição de Vídeo
- Concatenação de imagens com timing
- Fade in/out entre transições
- Título sobreposto com borda
- Áudio sincronizado
- Resolução 1080x1920 (vertical)

### ✅ Upload para B2
- Upload automático
- URLs assinadas (1h de validade)

---

## 📊 Parâmetros de Input

| Parâmetro | Tipo | Obrigatório | Padrão | Descrição |
|-----------|------|-------------|--------|-----------|
| `mode` | string | Não | - | "test" para teste de saúde |
| `topic` | string | Sim* | - | Tópico do vídeo |
| `script` | string | Sim* | - | Script customizado |
| `title` | string | Não | Auto | Título do vídeo |
| `style` | string | Não | "viral" | Estilo: viral, educational, story |
| `duration` | int | Não | 60 | Duração alvo em segundos |
| `num_images` | int | Não | 3 | Número de imagens |

*Pelo menos `topic` ou `script` deve ser fornecido.

---

## 🔧 Troubleshooting

### Worker dá exit code 1
- ✅ **Solução:** Dockerfile sem HEALTHCHECK (já corrigido)

### Erro "gTTS não disponível"
- ✅ **Solução:** `gtts>=2.5.0` adicionado ao requirements.txt

### Upload B2 falha
- Verifique as env vars: `B2_KEY_ID`, `B2_APP_KEY`, `B2_BUCKET_NAME`

---

## 📝 Changelog

### v2.0 (2024-12-11)
- ✅ Removido HEALTHCHECK que causava crash
- ✅ Adicionado gtts ao requirements.txt
- ✅ Handler completo com todas funcionalidades
- ✅ Geração de script com templates
- ✅ Composição de vídeo com título e transições
- ✅ Upload automático para B2

---

**Desenvolvido para RunPod Serverless** 🚀
