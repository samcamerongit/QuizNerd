import tempfile
import unittest
from pathlib import Path

from quiznerd import QuizDatabase, resolve_data_dir
from quiznerd_data import SEED_QUESTIONS


class QuizDatabaseTests(unittest.TestCase):
  def test_bootstrap_seeds_all_questions(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
      database = QuizDatabase(Path(temp_dir) / "quiznerd.db")
      questions = database.get_questions("general")

    self.assertEqual(len(questions), len(SEED_QUESTIONS))

  def test_true_false_questions_use_true_false_options(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
      database = QuizDatabase(Path(temp_dir) / "quiznerd.db")
      questions = database.get_questions("general")

    true_false = [question for question in questions if question["question_type"] == "true_false"]

    self.assertTrue(true_false)
    for question in true_false:
      self.assertEqual(question["options"], ["True", "False"])
      self.assertIn(question["answer"], question["options"])

  def test_multiple_choice_answers_stay_in_the_option_list(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
      database = QuizDatabase(Path(temp_dir) / "quiznerd.db")
      questions = database.get_questions("general")

    multiple_choice = [question for question in questions if question["question_type"] == "multiple_choice"]

    self.assertTrue(multiple_choice)
    for question in multiple_choice:
      self.assertEqual(len(question["options"]), 4)
      self.assertIn(question["answer"], question["options"])


class DataDirectoryTests(unittest.TestCase):
  def test_source_runs_store_data_beside_the_script(self) -> None:
    source_dir = Path("/tmp/quiznerd-source")
    self.assertEqual(resolve_data_dir(source_dir), source_dir)


if __name__ == "__main__":
  unittest.main()
