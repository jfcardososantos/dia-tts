from dia.model import Dia
from fastapi import FastAPI, Response
from pydantic import BaseModel
import soundfile as sf
import io

app = FastAPI()

model = Dia.from_pretrained("nari-labs/Dia-1.6B-0626", compute_dtype="float16")

class GenerationRequest(BaseModel):
    text: str
    use_torch_compile: bool = False
    verbose: bool = False
    cfg_scale: float = 3.0
    temperature: float = 1.8
    top_p: float = 0.90
    cfg_filter_top_k: int = 50

@app.post("/generate/")
async def generate_audio(request: GenerationRequest):
    output = model.generate(
        request.text,
        use_torch_compile=request.use_torch_compile,
        verbose=request.verbose,
        cfg_scale=request.cfg_scale,
        temperature=request.temperature,
        top_p=request.top_p,
        cfg_filter_top_k=request.cfg_filter_top_k,
    )

    buffer = io.BytesIO()
    sf.write(buffer, output['audio_samples'], output['sampling_rate'], format='WAV')
    buffer.seek(0)

    return Response(content=buffer.read(), media_type="audio/wav")
