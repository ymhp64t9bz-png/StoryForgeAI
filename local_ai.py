"""
🤖 Local AI Service - 100% Open Source
Integração com Ollama para geração de scripts usando LLMs locais
"""

import ollama
import logging
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)


class LocalAIService:
    """Serviço de IA Local usando Ollama"""
    
    def __init__(self, model: str = "llama3.1:8b"):
        """
        Inicializa o serviço de IA local
        
        Args:
            model: Nome do modelo Ollama (padrão: llama3.1:8b)
        """
        self.model = model
        self._check_ollama_connection()
    
    def _check_ollama_connection(self):
        """Verifica se o Ollama está rodando"""
        try:
            ollama.list()
            logger.info(f"✅ Ollama conectado! Modelo: {self.model}")
        except Exception as e:
            logger.error(f"❌ Erro ao conectar com Ollama: {e}")
            logger.warning("⚠️ Certifique-se de que o Ollama está rodando: 'ollama serve'")
    
    def generate_script(
        self,
        topic: str,
        style: str = "viral",
        duration: int = 60,
        platform: str = "tiktok"
    ) -> Dict[str, any]:
        """
        Gera um script para vídeo curto usando LLM local
        
        Args:
            topic: Tópico do vídeo
            style: Estilo do vídeo (viral, educativo, engraçado, etc.)
            duration: Duração alvo em segundos
            platform: Plataforma (tiktok, youtube, instagram)
        
        Returns:
            Dict com script, título, hashtags e cenas
        """
        
        prompt = self._build_script_prompt(topic, style, duration, platform)
        
        # Tenta gerar até 2 vezes
        max_retries = 2
        for attempt in range(max_retries):
            try:
                logger.info(f"🔄 Tentativa de geração {attempt + 1}/{max_retries}...")
                
                response = ollama.chat(
                    model=self.model,
                    messages=[
                        {
                            'role': 'system',
                            'content': 'Você é um roteirista profissional. Responda APENAS com JSON válido.'
                        },
                        {
                            'role': 'user',
                            'content': prompt
                        }
                    ],
                    options={
                        'temperature': 0.7,
                        'top_p': 0.9,
                        'num_ctx': 8192,     # Contexto aumentado drasticamente
                        'num_predict': 4096, # Permitir resposta muito longa
                    }
                )
                
                content = response['message']['content']
                
                # Tenta limpar o conteúdo para encontrar JSON
                json_content = self._extract_json_from_text(content)
                
                if json_content:
                    result = json.loads(json_content)
                    
                    # Valida se tem campos obrigatórios
                    if "script" in result and len(result.get("script", "").split()) > 50:
                        logger.info(f"✅ Script gerado com sucesso na tentativa {attempt + 1}")
                        return result
                    else:
                        logger.warning(f"⚠️ JSON gerado, mas script muito curto. Tentando novamente...")
                
            except Exception as e:
                logger.error(f"❌ Erro na tentativa {attempt + 1}: {e}")
                
        # Se falhar todas as tentativas, usa fallback, mas com aviso
        logger.error("❌ Falha em todas as tentativas de geração. Usando fallback.")
        return self._get_fallback_script(topic, style)

    def _extract_json_from_text(self, text: str) -> Optional[str]:
        """Tenta encontrar e extrair bloco JSON dentro de um texto"""
        try:
            # Procura pelo primeiro '{' e último '}'
            start = text.find('{')
            end = text.rfind('}')
            
            if start != -1 and end != -1:
                return text[start:end+1]
            return None
        except:
            return None
    
    def _build_script_prompt(
        self,
        topic: str,
        style: str,
        duration: int,
        platform: str
    ) -> str:
        """Constrói o prompt para geração de script"""
        
        # LÓGICA MATEMÁTICA OBRIGATÓRIA
        # 2.5 palavras por segundo é a média padrão de fala confortável
        words_count_min = int(duration * 2.3)
        words_count_target = int(duration * 2.5)
        
        # Calcula número de cenas baseado na duração
        num_scenes = max(3, duration // 12)
        scene_duration = duration // num_scenes
        
        prompt = f"""
Você é um roteirista profissional de elite.

TAREFA: Escrever um roteiro para vídeo de EXATAMENTE {duration} segundos.
TÓPICO: "{topic}"

⚠️ REGRA MATEMÁTICA DE OURO (Siga ou o script falhará):
Para preencher {duration} segundos, você PRECISA escrever entre {words_count_min} e {words_count_target} palavras.
NÃO escreva menos que {words_count_min} palavras sob nenhuma circunstância.

ESTRUTURA OBRIGATÓRIA (JSON VÁLIDO):
{{
  "titulo": "Título Viral (Max 50 chars)",
  "script": "Texto COMPLETO da narração. DEVE ter pelo menos {words_count_min} palavras.",
  "cenas": [
    {{
      "visual": "Descrição visual DETALHADA em inglês (Prompt para Stable Diffusion)",
      "narração": "Trecho da narração correspondente a esta cena (~{scene_duration}s)"
    }}
  ]
}}

REQUISITOS DE CONTEÚDO:
1. Estilo: {style.upper()}
2. Plataforma: {platform.upper()}
3. O script deve ser denso, informativo e direto. Sem "Olá pessoal" ou introduções longas.
4. Divida em exatamente {num_scenes} cenas.
5. As descrições visuais DEVEM ser em INGLÊS, detalhadas e cinematográficas (ex: "Cinematic shot of..., 8k, unreal engine").

Responda APENAS com o JSON.
"""
        return prompt
    
    def _parse_text_response(self, text: str, topic: str) -> Dict:
        """Parseia resposta em texto puro caso não seja JSON"""
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        return {
            "titulo": f"{topic} - Você Precisa Ver Isso!",
            "gancho": lines[0] if lines else "Você não vai acreditar nisso!",
            "script": text,
            "cta": "Curte e segue para mais!",
            "hashtags": [f"#{topic.lower().replace(' ', '')}", "#viral", "#fyp"],
            "cenas": [
                {
                    "tempo": "0-60s",
                    "narração": text,
                    "visual": f"Imagens relacionadas a {topic}"
                }
            ]
        }
    
    def _get_fallback_script(self, topic: str, style: str) -> Dict:
        """Script de fallback caso a IA falhe"""
        
        return {
            "titulo": f"{topic.title()} - Inacreditável!",
            "gancho": f"Você sabia que {topic.lower()} pode mudar tudo?",
            "script": f"Hoje vou te mostrar algo incrível sobre {topic}. Isso vai mudar completamente sua perspectiva. Fica até o final que você vai se surpreender!",
            "cta": "Curte e segue para mais conteúdos incríveis!",
            "hashtags": [f"#{topic.lower().replace(' ', '')}", "#viral", "#fyp", "#brasil"],
            "cenas": [
                {
                    "tempo": "0-20s",
                    "narração": f"Você sabia que {topic.lower()} pode mudar tudo?",
                    "visual": f"Imagem impactante sobre {topic}"
                },
                {
                    "tempo": "20-40s",
                    "narração": "Hoje vou te mostrar algo incrível sobre isso.",
                    "visual": "Demonstração visual"
                },
                {
                    "tempo": "40-60s",
                    "narração": "Curte e segue para mais conteúdos incríveis!",
                    "visual": "CTA visual"
                }
            ]
        }
    
    def generate_title(self, script: str, style: str = "viral") -> str:
        """
        Gera um título viral para o vídeo
        
        Args:
            script: Script do vídeo
            style: Estilo do título
        
        Returns:
            Título otimizado
        """
        
        prompt = f"""
Crie um título VIRAL e CLICKBAIT para este vídeo:

Script: "{script[:200]}..."

Regras:
- Máximo 60 caracteres
- Português do Brasil
- Estilo: {style}
- Usar emojis estratégicos
- Gerar curiosidade/urgência
- Não usar pontos finais

Responda APENAS com o título, sem aspas ou explicações.
"""
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0.9}
            )
            
            title = response['message']['content'].strip().strip('"\'')
            return title[:60]  # Limita a 60 caracteres
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar título: {e}")
            return "Você Não Vai Acreditar Nisso! 😱"
    
    def improve_script(self, script: str, feedback: str) -> str:
        """
        Melhora um script existente baseado em feedback
        
        Args:
            script: Script original
            feedback: Feedback do usuário
        
        Returns:
            Script melhorado
        """
        
        prompt = f"""
Script Original:
{script}

Feedback do Usuário:
{feedback}

Reescreva o script incorporando o feedback, mantendo o estilo viral e envolvente.
Responda APENAS com o novo script, sem explicações.
"""
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}]
            )
            
            return response['message']['content'].strip()
            
        except Exception as e:
            logger.error(f"❌ Erro ao melhorar script: {e}")
            return script  # Retorna o original se falhar


# Instância global do serviço
_ai_service = None

def get_ai_service(model: str = "llama3.1:8b") -> LocalAIService:
    """Retorna instância singleton do serviço de IA"""
    global _ai_service
    if _ai_service is None:
        _ai_service = LocalAIService(model=model)
    return _ai_service


# Funções de conveniência
def generate_script(topic: str, **kwargs) -> Dict:
    """Atalho para gerar script"""
    service = get_ai_service()
    return service.generate_script(topic, **kwargs)


def generate_title(script: str, **kwargs) -> str:
    """Atalho para gerar título"""
    service = get_ai_service()
    return service.generate_title(script, **kwargs)
