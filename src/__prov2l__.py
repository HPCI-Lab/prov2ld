import json
import os
import argparse

def get_json_files(path: str) -> list:
    """Recursively finds all .json files in a directory or returns the file itself."""
    if os.path.isfile(path):
        return [path]
    
    json_files = []
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))
    return json_files

def main():
    parser = argparse.ArgumentParser(
        description='Convert PROV-JSON files into a single-line-per-file JSONL',
    )
    
    parser.add_argument('input', type=str, help='Input PROV-JSON file or directory')
    parser.add_argument('output', type=str, help='Output JSONL file path')
    
    args = parser.parse_args()
    
    input_files = get_json_files(args.input)
    
    if not input_files:
        print(f"Error: No JSON files found at {args.input}")
        return

    processed_count = 0
    with open(args.output, 'w', encoding='utf-8') as out_f:
        for file_path in input_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as in_f:
                    # Load the full data structure
                    data = json.load(in_f)
                    
                    # Dump the entire object to one string (no newlines)
                    # and write as a single line in the output
                    json_line = json.dumps(data, ensure_ascii=False)
                    out_f.write(json_line + "\n")
                    processed_count += 1
                    
            except (json.JSONDecodeError, IOError) as e:
                print(f"Skipping {file_path} due to error: {e}")

    print(f"Done: {processed_count} files merged into {args.output}")

if __name__ == '__main__':
    main()