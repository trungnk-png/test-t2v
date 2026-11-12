import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


class PromptFlowTests(unittest.TestCase):
    def test_demo_prompt_enters_guard_and_preserves_downstream_links(self):
        path = Path(__file__).resolve().parents[1] / 'workflow_text_only.json'
        original = json.loads(path.read_text())
        with patch.object(app, 'WORKFLOW_PATH', path):
            workflow = app.configure_workflow('A bird flying', 3, 42, 'test')
        self.assertEqual(workflow['prompt_guard']['inputs']['prompt'], 'A bird flying')
        self.assertEqual(workflow['93']['inputs']['prompt'], ['prompt_guard', 0])
        self.assertEqual(workflow['140_131']['inputs']['prompt'], ['93', 0])
        for node_id, node in original.items():
            for key, value in node['inputs'].items():
                if isinstance(value, list):
                    self.assertEqual(workflow[node_id]['inputs'][key], value)
        self.assertEqual(workflow['93']['inputs']['style'], original['93']['inputs']['style'])

    def test_default_demo_duration_is_exactly_three_seconds(self):
        request = app.GenerateRequest(prompt='A bird flying')
        self.assertEqual(request.duration, 3)
        workflow = app.configure_workflow(request.prompt, request.duration, 42, 'test')
        duration = workflow['140_133']['inputs']['value']
        fps = workflow['140_130']['inputs']['fps']
        # Evaluate the workflow's actual arithmetic expressions.
        generated = eval(workflow['140_132']['inputs']['expression'],
                         {'__builtins__': {}, 'max': max, 'round': round}, {'a': duration})
        output = eval(workflow['output_frame_count']['inputs']['expression'],
                      {'__builtins__': {}, 'max': max, 'round': round}, {'a': duration})
        self.assertEqual(generated % 17, 5)
        self.assertGreaterEqual(generated, output)
        self.assertEqual(output, 48)
        self.assertEqual(output / fps, 3)
        self.assertEqual(workflow['trim_output_frames']['inputs']['image'], ['140_122', 0])
        self.assertEqual(workflow['trim_output_frames']['inputs']['length'], ['output_frame_count', 1])
        self.assertEqual(workflow['140_130']['inputs']['images'], ['trim_output_frames', 0])

    def test_missing_guard_rejects_workflow(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'workflow.json'
            path.write_text(json.dumps({'generator': {
                'class_type': 'MiniMaxH3ImageToVideo', 'inputs': {'prompt': 'old prompt'},
            }}))
            with patch.object(app, 'WORKFLOW_PATH', path):
                with self.assertRaisesRegex(RuntimeError, 'DetectNSFWText'):
                    app.configure_workflow('new prompt', 3, 42, 'test')


if __name__ == '__main__':
    unittest.main()
