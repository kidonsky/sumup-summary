import sumup_summary
import filecmp
import os


test_folder = "test_files/"
test_cleaned_file = test_folder + "test_cleanedFile.csv"
complete_file = test_folder + "testReport.csv"
new_file = test_folder + "toto"


def test_cleaning():
    assert sumup_summary.clean_file(complete_file, new_file) == 0
    assert os.path.isfile(new_file)
    assert filecmp.cmp(test_cleaned_file, new_file)
    os.remove(new_file)
