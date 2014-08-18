##########################
# Test the evaluation module
##########################

from util import (config_doc_kw_model, NumericTestCase)

from scinet3.util.ir_eval import GoalBasedEvaluator
from scinet3.model import (Document, Keyword)


config_doc_kw_model()
Document.load_all_from_db()

class GoalBasedEvaluationTest(NumericTestCase):
    def setUp(self):
        doc_goal = Document.get_many([1,2])
        kw_goal = Keyword.get_many(["redis", "database"])
        
        self.e = GoalBasedEvaluator()

        self.e.setGoal(doc_goal, kw_goal)

    def test_one(self):
        docs = [Document.get_many([1,2]), Document.get_many([1,2]), Document.get_many([2,1])]
        kws = [Keyword.get_many(["redis", "database"]), Keyword.get_many(["redis", "database"]), Keyword.get_many(["redis", "database"])]

        scores = self.e.evaluate(docs, kws)
        expected = ([1,1,1], [1,1,1])
        
        self.assertArrayAlmostEqual(expected[0], scores[0])
        self.assertArrayAlmostEqual(expected[1], scores[1])


    def test_two(self):
        docs = [Document.get_many([8,10]), Document.get_many([3,4]), Document.get_many([2,1])]
        kws = [Keyword.get_many(["a", "the"]), Keyword.get_many(["python", "database"]), Keyword.get_many(["database", "redis"])]

        scores = self.e.evaluate(docs, kws)
        expected = ([0.34491169135422844, 0.1726882003112921, 1.0],
                    [0.4834283906452939, 0.759679156743632, 0.9999999999999999])

        self.assertArrayAlmostEqual(expected[0], scores[0])
        self.assertArrayAlmostEqual(expected[1], scores[1])
