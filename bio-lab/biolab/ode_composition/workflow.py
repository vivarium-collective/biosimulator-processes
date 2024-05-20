import os

import dotenv
import openai
from transformers import GPT2LMHeadModel, GPT2Tokenizer


# Set your API key for OpenAI
dotenv.load_dotenv()
openai.api_key = os.environ["OPENAI_SECRET"]

# Initialize the local GPT model
MODEL_NAME = 'gpt2'  # You can use 'gpt2-medium', 'gpt2-large', etc.
MODEL = GPT2LMHeadModel.from_pretrained(MODEL_NAME)
TOKENIZER = GPT2Tokenizer.from_pretrained(MODEL_NAME)


# Function to generate a response using OpenAI API
def call_openai_gpt(prompt):
    response = openai.Completion.create(
        engine="davinci-codex",  # Use the custom model name if available
        prompt=prompt,
        max_tokens=1500
    )
    return response.choices[0].text.strip()


# Function to generate a response using local GPT model
def call_local_gpt(prompt):
    inputs = TOKENIZER.encode(prompt, return_tensors='pt')
    outputs = MODEL.generate(inputs, max_length=1500, num_return_sequences=1)
    response = TOKENIZER.decode(outputs[0], skip_special_tokens=True)
    return response


# Function to fetch PubMed article details
def get_pubmed_article(article_id, use_local=False):
    prompt = f"Here is an article id from PubMed: {article_id}. Please find the article and summarize it."
    if use_local:
        return call_local_gpt(prompt)
    else:
        return call_openai_gpt(prompt)


# Function to generate SBML model from article details
def generate_sbml(article_details, use_local=False):
    prompt = f"Based on the following article details, create an SBML model file and provide reasoning for each declaration:\n\n{article_details}"
    if use_local:
        sbml_response = call_local_gpt(prompt)
    else:
        sbml_response = call_openai_gpt(prompt)
    sbml_model, reasoning = sbml_response.split("Reasoning:", 1)
    return sbml_model.strip(), reasoning.strip()


# Function to create a BioSimulator composition
def create_biosimulator_composition(sbml_model, use_local=False):
    prompt = f"Using the following SBML model, create a BioSimulator Processes composition and provide reasoning:\n\n{sbml_model}"
    if use_local:
        composition_response = call_local_gpt(prompt)
    else:
        composition_response = call_openai_gpt(prompt)
    composition, reasoning = composition_response.split("Reasoning:", 1)
    return composition.strip(), reasoning.strip()


# Function to run the composite simulation
def run_simulation(composition, use_local=False):
    prompt = f"Run the following composite simulation and provide the results over time:\n\n{composition}"
    if use_local:
        results_response = call_local_gpt(prompt)
    else:
        results_response = call_openai_gpt(prompt)
    results, reasoning = results_response.split("Reasoning:", 1)
    return results.strip(), reasoning.strip()


# Function to verify the simulation output
def verify_output(results, use_local=False):
    prompt = f"Verify the output of the following simulation results:\n\n{results}"
    if use_local:
        verification_response = call_local_gpt(prompt)
    else:
        verification_response = call_openai_gpt(prompt)
    verification, reasoning = verification_response.split("Reasoning:", 1)
    return verification.strip(), reasoning.strip()
