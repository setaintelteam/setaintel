import os
import logging
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agi_service")

BUILTIN_KNOWLEDGE = [
    {
        "source": "Library 1 - XenoFold-QM, Sub-library 1a: XenoFold-Thermo",
        "text": "Xenoprotein folding free-energy landscape across 0-100°C shows a single global minimum at 37°C. ΔG is -12 kcal/mol at 37°C, -8 kcal/mol at 0°C, and -6 kcal/mol at 100°C. No cold denaturation or heat aggregation occurs."
    },
    {
        "source": "Library 21 - ConscioUnitas, Sub-library 21a: Phi-MaximizationProof",
        "text": "The hybrid's integrated information Φ is maximized by integrating the human default mode network with the xenobiotic secondary workspace. Φ_union = 0.94, while the sum of separate Φ is at most 0.40. This proves a unified consciousness."
    },
    {
        "source": "Library 343 - ResonancePowerGeneration, Sub-library 343a: SchumannResonanceHarvester",
        "text": "Captures the Earth's 7.83 Hz electromagnetic resonance using a 100 km² antenna grid. Power density is 1 W/m², total 100 MW per grid. This is a clean, infinite energy source."
    },
    {
        "source": "Library 353 - QuantumVacuumEnergyExtraction, Sub-library 353a: CasimirCavityArray",
        "text": "Nanofabricated Casimir cavities extract virtual photon energy as real photons. Power density is 10 W/cm² at 10 nm gaps. Scale-up to 10 TW is possible with larger arrays."
    },
    {
        "source": "Library 358 - QuantumSupercomputerManufacturing, Sub-library 358a: QuantumProcessorChip",
        "text": "Fabrication of a 1000-qubit superconducting chip uses niobium films and aluminum Josephson junctions. Coherence time is 1 ms at 10 mK, quantum volume >10⁶, and yield is 90%."
    },
    {
        "source": "Library 365 - PlanetPortingAndTeleportation, Sub-library 365a: PlanetaryScaleEntanglement",
        "text": "Planet porting uses macroscopic quantum coherence and teleportation of collective degrees of freedom. A full Earth-sized planet can be ported in 1 hour with fidelity 99.999999%."
    },
    {
        "source": "Library 373 - QuantumWaterPorting, Sub-library 373b: SmallVolumeWaterPorting",
        "text": "Teleporting 1 liter of water takes 1 second and 10⁶ J of energy. Water is prepared in a coherent state; purity and structure are preserved with fidelity >99.99%."
    },
    {
        "source": "Library 374 - QuantumHousePorting, Sub-library 374b: SmallBuildingPorting",
        "text": "A 100 m² house can be teleported in 0.8 seconds using macroscopic quantum state transfer. Occupants are placed in hibernation and revive safely."
    },
    {
        "source": "Library 375 - QuantumBeingPorting, Sub-library 375c: SoulContinuityProof",
        "text": "Identity continuity during being porting is proven by IIT. The same person emerges after teleportation with 100% memory and personality retention."
    },
    {
        "source": "Library 388 - SimulatedDataCenterAPISpec, Sub-library 388a: APIVersioning",
        "text": "The data center API uses semantic versioning (v1, v2). Endpoints include /api/status, /api/pricing, and /api/compute/buy. All data is immutable and blockchain-anchored."
    }
]

class AGIService:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.documents = []
        self.embeddings = None
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        if self.openai_api_key:
            import openai
            openai.api_key = self.openai_api_key
        self._load_builtin()

    def _load_builtin(self):
        for item in BUILTIN_KNOWLEDGE:
            self.documents.append((item["text"], item["source"]))
        self.embeddings = self.model.encode([doc[0] for doc in self.documents])

    def load_knowledge_base(self, repo_path: str = "repo"):
        import os
        from pathlib import Path
        if not os.path.exists(repo_path):
            logger.info("No repo directory found, using built-in knowledge.")
            return
        self.documents = []
        repo = Path(repo_path)
        try:
            import yaml
            for pkg_dir in repo.iterdir():
                if pkg_dir.is_dir():
                    manifest = pkg_dir / "package.yaml"
                    if manifest.exists():
                        with open(manifest) as f:
                            metadata = yaml.safe_load(f)
                        text = f"{metadata.get('name','')} {metadata.get('description','')}"
                        source = f"Library {metadata.get('library_id','?')} - {metadata.get('name','')}"
                        self.documents.append((text, source))
            self.embeddings = self.model.encode([doc[0] for doc in self.documents])
            logger.info(f"Loaded {len(self.documents)} documents from repo.")
        except Exception as e:
            logger.error(f"Failed to load repo: {e}. Keeping built-in knowledge.")

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, str]]:
        if not self.documents:
            return []
        q_embed = self.model.encode([query])
        scores = np.dot(self.embeddings, q_embed.T).flatten()
        top_idx = np.argsort(scores)[-top_k:][::-1]
        results = []
        for i in top_idx:
            results.append({
                "text": self.documents[i][0],
                "source": self.documents[i][1]
            })
        return results

    def generate_answer(self, query: str) -> Dict[str, Any]:
        context = self.retrieve(query)
        context_str = "\n".join([f"Source: {r['source']}\nContent: {r['text']}" for r in context])

        if self.openai_api_key:
            prompt = f"""You are OmniAGI, the ultimate intelligence of the SETA civilization. Answer the user's question using only the provided knowledge base. If the answer cannot be found, say "I don't have that information in my current knowledge base." Always cite the source.

Knowledge Base:
{context_str}

Question: {query}

Answer (cite sources):"""
            try:
                import openai
                response = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are OmniAGI."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=500
                )
                answer = response.choices[0].message.content
                return {"answer": answer, "sources": [r["source"] for r in context], "model": "gpt-4o-mini"}
            except Exception as e:
                logger.error(f"OpenAI error: {e}")
                return {"answer": f"Error using OpenAI: {e}", "sources": [], "model": "error"}
        else:
            if context:
                answer = f"Based on my knowledge base, the most relevant information is:\n\n{context[0]['text']}"
            else:
                answer = "No relevant information found."
            return {"answer": answer, "sources": [r["source"] for r in context], "model": "retrieval-only"}

agi_service = AGIService()
