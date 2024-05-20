from biolab.ode_composition import workflow as wf


def main(pubmed_id, use_local=False):
    article_details = wf.get_pubmed_article(pubmed_id, use_local)
    print("Article Details:", article_details)

    sbml_model, sbml_reasoning = wf.generate_sbml(article_details, use_local)
    print("SBML Model:", sbml_model)
    print("Reasoning:", sbml_reasoning)

    composition, composition_reasoning = wf.create_biosimulator_composition(sbml_model, use_local)
    print("Composition:", composition)
    print("Reasoning:", composition_reasoning)

    results, results_reasoning = wf.run_simulation(composition, use_local)
    print("Simulation Results:", results)
    print("Reasoning:", results_reasoning)

    verification, verification_reasoning = wf.verify_output(results, use_local)
    print("Verification:", verification)
    print("Reasoning:", verification_reasoning)


# Example usage
def test_main():
    pubmed_id = "33108355"
    main(pubmed_id)


if __name__ == '__main__':
    test_main()
