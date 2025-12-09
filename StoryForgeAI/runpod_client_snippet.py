
def processar_story_forge(topico, duracao=60, voice="pt-BR-AntonioNeural"):
    """
    Função Client-Side para chamar a StoryForge AI no RunPod.
    """
    endpoint_id = "SEU_ENDPOINT_STORYFORGE_AQUI" 
    
    payload = {
        "input": {
            "topic": topico,
            "duration": duracao,
            "voice": voice
        }
    }
    
    print(f"🚀 Iniciando geração de story: {topico}...")
    
    try:
        endpoint = runpod.Endpoint(endpoint_id)
        run_request = endpoint.run(payload)
        
        # Bloqueia até terminar (Polling)
        result = run_request.output()
        
        if result and result.get("status") == "success":
            print(f"✅ Vídeo gerado com sucesso!")
            print(f"📂 Caminho: {result.get('video_path')}")
            return result
        else:
            print(f"❌ Erro na geração: {result}")
            return None
            
    except Exception as e:
        print(f"❌ Erro de conexão RunPod: {e}")
        return None
