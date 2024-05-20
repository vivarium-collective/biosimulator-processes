from biolab.ode_composition.fetch_article import fetch_article
from biolab.ode_composition.parse_article import parse_article
from biolab.ode_composition.create_sbml import create_sbml_model
from biolab.ode_composition.generate_composition import generate_composition
from biolab.ode_composition.run_composition import run_composition
from biolab.ode_composition.verify_output import verify_output
from libsbml import writeSBML


def main(pubmed_id):
    # Fetch the article
    article_html = fetch_article(pubmed_id)

    # Parse the article
    article_info = parse_article(article_html)

    # Create SBML model
    sbml_document = create_sbml_model(article_info)
    sbml_file = 'example_model.xml'
    writeSBML(sbml_document, sbml_file)

    # Generate composition
    composition = generate_composition(sbml_file)

    # Run simulation
    simulation_results = run_composition(composition)

    # Verify output
    verified_results = verify_output(simulation_results)

    # Display results
    print("Article Info:", article_info)
    print("Composition:", composition)
    print("Simulation Results:", simulation_results)
    print("Verified Results:", verified_results)


# Example usage
def test_main():
    pubmed_id = "33108355"  # Replace with actual PubMed ID
    main(pubmed_id)
