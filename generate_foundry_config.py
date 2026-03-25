from transformers import AutoTokenizer
import json
import os

def generate_config(model_id, output_path, name):
    print(f"Generating config for {name} from {model_id}...")
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    
    # Simple template extraction or fallback
    # Qwen uses specific template, DeepSeek likely similar.
    # We will simply ask the tokenizer to render a template and replace the content with placeholder.
    
    try:
        # Use a dummy apply to see what it produces
        dummy_prompt = tokenizer.apply_chat_template(
            [{"role": "user", "content": "{Content}"}], 
            tokenize=False, 
            add_generation_prompt=True
        )
        # Verify placeholder exists
        if "{Content}" not in dummy_prompt:
             # Sometimes tokenizer escapes it.
             print("Warning: {Content} placeholder lost in template application.")
    except:
        # Fallback for models without strict chat template
        dummy_prompt = "<|im_start|>user\n{Content}<|im_end|>\n<|im_start|>assistant\n"

    json_template = {
        "Name": name,
        "PromptTemplate": {
            "assistant": "{Content}",
            "prompt": dummy_prompt
        }
    }
    
    config_path = os.path.join(output_path, "inference_model.json")
    with open(config_path, "w") as f:
        json.dump(json_template, f, indent=2)
    print(f"Saved to {config_path}")

generate_config("models/source/qwen", "models/qwen-reflex", "qwen-reflex")
generate_config("models/source/deepseek", "models/deepseek-reason", "deepseek-reason")
