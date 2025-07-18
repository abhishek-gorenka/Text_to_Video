# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import os

import torch

from cosmos1.models.diffusion.inference.inference_utils import add_common_arguments, validate_args
from cosmos1.models.diffusion.inference.world_generation_pipeline import DiffusionText2WorldGenerationPipeline
from cosmos1.utils import log, misc
from cosmos1.utils.io import read_prompts_from_file, save_video

torch.enable_grad(False)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Text to world generation demo script")
    # Add common arguments
    add_common_arguments(parser)

#     parser.add_argument(
#     "--seed", type=int, default=42, help="Random seed for reproducibility"
# )

    # Add text2world specific arguments
    parser.add_argument(
        "--diffusion_transformer_dir",
        type=str,
        default="Cosmos-1.0-Diffusion-7B-Text2World",
        help="DiT model weights directory name relative to checkpoint_dir",
        choices=[
            "Cosmos-1.0-Diffusion-7B-Text2World",
            "Cosmos-1.0-Diffusion-14B-Text2World",
        ],
    )
    parser.add_argument(
        "--prompt_upsampler_dir",
        type=str,
        default="Cosmos-1.0-Prompt-Upsampler-12B-Text2World",
        help="Prompt upsampler weights directory relative to checkpoint_dir",
    )

    parser.add_argument(
        "--word_limit_to_skip_upsampler",
        type=int,
        default=250,
        help="Skip prompt upsampler for better robustness if the number of words in the prompt is greater than this value",
    )

    return parser.parse_args()


def demo(cfg):
    """Run text-to-world generation demo.

    This function handles the main text-to-world generation pipeline, including:
    - Setting up the random seed for reproducibility
    - Initializing the generation pipeline with the provided configuration
    - Processing single or multiple prompts from input
    - Generating videos from text prompts
    - Saving the generated videos and corresponding prompts to disk

    Args:
        cfg (argparse.Namespace): Configuration namespace containing:
            - Model configuration (checkpoint paths, model settings)
            - Generation parameters (guidance, steps, dimensions)
            - Input/output settings (prompts, save paths)
            - Performance options (model offloading settings)

    The function will save:
        - Generated MP4 video files
        - Text files containing the processed prompts

    If guardrails block the generation, a critical log message is displayed
    and the function continues to the next prompt if available.
    """
    misc.set_random_seed(cfg.seed)
    inference_type = "text2world"
    validate_args(cfg, inference_type)

    # Initialize text2world generation model pipeline
    pipeline = DiffusionText2WorldGenerationPipeline(
        inference_type=inference_type,
        checkpoint_dir=cfg.checkpoint_dir,
        checkpoint_name=cfg.diffusion_transformer_dir,
        prompt_upsampler_dir=cfg.prompt_upsampler_dir,
        enable_prompt_upsampler=not cfg.disable_prompt_upsampler,
        offload_network=cfg.offload_diffusion_transformer,
        offload_tokenizer=cfg.offload_tokenizer,
        offload_text_encoder_model=cfg.offload_text_encoder_model,
        offload_prompt_upsampler=cfg.offload_prompt_upsampler,
        offload_guardrail_models=cfg.offload_guardrail_models,
        guidance=cfg.guidance,
        num_steps=cfg.num_steps,
        height=cfg.height,
        width=cfg.width,
        fps=cfg.fps,
        num_video_frames=cfg.num_video_frames,
        seed=cfg.seed,
    )

    # Handle multiple prompts if prompt file is provided
    if cfg.batch_input_path:
        log.info(f"Reading batch inputs from path: {args.batch_input_path}")
        prompts = read_prompts_from_file(cfg.batch_input_path)
    else:
        # Single prompt case
        prompts = [{"prompt": cfg.prompt}]

    os.makedirs(cfg.video_save_folder, exist_ok=True)
    for i, input_dict in enumerate(prompts):
        current_prompt = input_dict.get("prompt", None)
        if current_prompt is None:
            log.critical("Prompt is missing, skipping world generation.")
            continue

        # Generate video
        generated_output = pipeline.generate(current_prompt, cfg.negative_prompt, cfg.word_limit_to_skip_upsampler)
        if generated_output is None:
            log.critical("Guardrail blocked text2world generation.")
            continue
        video, prompt = generated_output

        if cfg.batch_input_path:
            video_save_path = os.path.join(cfg.video_save_folder, f"{i}.mp4")
            prompt_save_path = os.path.join(cfg.video_save_folder, f"{i}.txt")
        else:
            video_save_path = os.path.join(cfg.video_save_folder, f"{cfg.video_save_name}.mp4")
            prompt_save_path = os.path.join(cfg.video_save_folder, f"{cfg.video_save_name}.txt")

        # Save video
        save_video(
            video=video,
            fps=cfg.fps,
            H=cfg.height,
            W=cfg.width,
            video_save_quality=5,
            video_save_path=video_save_path,
        )

        # Save prompt to text file alongside video
        with open(prompt_save_path, "wb") as f:
            f.write(prompt.encode("utf-8"))

        log.info(f"Saved video to {video_save_path}")
        log.info(f"Saved prompt to {prompt_save_path}")


if __name__ == "__main__":
    args = parse_arguments()
    demo(args)
