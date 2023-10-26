import sumup_summary
import filecmp
import os


test_folder = "test_files/"
test_cleaned_file = test_folder + "test_cleanedFile.csv"
test_extracted_file = test_folder + "test_extractedFile.csv"
complete_file = test_folder + "testReport.csv"
new_file = test_folder + "toto"
config_file = "categories.toml"

verified_data_extracted = {
    "July": {"Adh[e,é]sio": 5, "Alcool|Bière": 31.5},
    "September": {"Adh[e,é]sio": 25, "Alcool|Bière": 32.5},
}


def test_cleaning():
    try:
        os.remove(new_file)
    except Exception as e:
        pass
    assert sumup_summary.rm_csv_rows(complete_file, new_file) == 0
    assert os.path.isfile(new_file)
    assert filecmp.cmp(test_cleaned_file, new_file)
    os.remove(new_file)


def test_extract():
    assert (
        sumup_summary.extract_data_from_file(test_extracted_file, config_file)
        == verified_data_extracted
    )
