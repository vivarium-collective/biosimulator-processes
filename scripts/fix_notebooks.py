import nbformat
import os


def fix_execution_count(notebook_path):
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)

    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            if 'execution_count' not in cell:
                cell['execution_count'] = None
            print('execution_count' in cell)

    with open(notebook_path, 'w', encoding='utf-8') as f:
        nbformat.write(nb, f)


if __name__ == '__main__':
    root = "composer-notebooks"
    for f in os.listdir(root):
        fp = os.path.join(root, f)
        print(fp)
        if not os.path.isdir(fp):
            fix_execution_count(fp)
