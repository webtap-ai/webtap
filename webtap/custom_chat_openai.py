from langchain.chat_models import ChatOpenAI
from typing import Dict, Any, List, Optional

# from langchain.llms import LLMResult, Generation


class CustomChatOpenAI(ChatOpenAI):
    seed: Optional[int] = None

    def __init__(self, seed=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seed = 123

    @property
    def _default_params(self) -> Dict[str, Any]:
        """Get the default parameters for calling OpenAI API."""
        return {
            "model": self.model_name,
            "request_timeout": self.request_timeout,
            "max_tokens": self.max_tokens,
            "stream": self.streaming,
            "n": self.n,
            "temperature": self.temperature,
            "seed": self.seed,
            **self.model_kwargs,
        }

    def __call__(self, messages):
        # Add the seed to the API call
        return super().__call__(messages, seed=self.seed)


'''
        def create_llm_result(
        self,
        choices: Any,
        prompts: List[str],
        token_usage: Dict[str, int],
        *,
        system_fingerprint: Optional[str] = None,
    ) -> LLMResult:
        """Create the LLMResult from the choices and prompts."""
        generations = []
        for i, _ in enumerate(prompts):
            sub_choices = choices[i * self.n : (i + 1) * self.n]
            generations.append(
                [
                    Generation(
                        text=choice["text"],
                        generation_info=dict(
                            finish_reason=choice.get("finish_reason"),
                            logprobs=choice.get("logprobs"),
                            system_fingerprint=system_fingerprint,  # Add this line
                        ),
                    )
                    for choice in sub_choices
                ]
            )
        llm_output = {"token_usage": token_usage, "model_name": self.model_name}
        if system_fingerprint:
            llm_output["system_fingerprint"] = system_fingerprint
        return LLMResult(generations=generations, llm_output=llm_output)
'''
