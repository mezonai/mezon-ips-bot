import zipfile
import re
import os


def clean_docx(file_path):
    print(f"Cleaning {file_path}...")
    temp_file = file_path + ".tmp"

    with zipfile.ZipFile(file_path, "r") as zin:
        with zipfile.ZipFile(temp_file, "w") as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "word/document.xml":
                    xml = data.decode("utf-8")

                    # Using safe negative lookahead regex to match exactly one placeholder
                    # without crossing boundaries.
                    pattern = r"\{\{(?:(?!\{\{|\}\}).)*?\}\}"

                    def replace_broken_placeholder(match):
                        raw_match = match.group(0)
                        # Strip all XML tags to get plain text representation
                        clean_text = re.sub(r"<[^>]+>", "", raw_match)
                        # Normalize internal spacing
                        clean_text = re.sub(r"\s+", " ", clean_text).strip()
                        print(f"  Fixed: {repr(clean_text)}")
                        return clean_text

                    xml_cleaned = re.sub(
                        pattern, replace_broken_placeholder, xml, flags=re.DOTALL
                    )
                    data = xml_cleaned.encode("utf-8")
                zout.writestr(item, data)

    os.replace(temp_file, file_path)
    print("Done!")


if __name__ == "__main__":
    templates = ["template/Template_HDCG.docx", "template/Template_BBNT.docx"]
    for t in templates:
        if os.path.exists(t):
            clean_docx(t)
        else:
            print(f"File not found: {t}")
