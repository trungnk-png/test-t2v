import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app
from video_safety import UnsafeVideoError


class PlaybackGateTests(unittest.TestCase):
    def run_render(self, result=None):
        job_id = 'test-gate'
        response = Mock()
        response.json.return_value = {'prompt_id': 'prompt'}
        response.iter_content.return_value = [b'video']
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        history = Mock()
        history.json.return_value = {'prompt': {
            'status': {'completed': True},
            'outputs': {'1': {'videos': [{'filename': 'test.mp4'}]}},
        }}
        with tempfile.TemporaryDirectory() as temp:
            app.jobs[job_id] = {'id': job_id, 'status': 'running', 'video_url': None}
            with patch.object(app, 'OUTPUT_DIR', Path(temp)), \
                 patch.object(app, 'configure_workflow', return_value={}), \
                 patch.object(app.requests, 'post', return_value=response), \
                 patch.object(app.requests, 'get', side_effect=[history, response]), \
                 patch.object(app, 'check_video', side_effect=result, return_value=15):
                app.render_job(job_id, app.GenerateRequest(prompt='test video'))
            job = app.jobs[job_id]
            if result:
                self.assertEqual(job['status'], 'error')
                self.assertFalse(job['safety_passed'])
                self.assertIsNone(job['video_url'])
                self.assertFalse(list(Path(temp).glob('*')))
                with self.assertRaises(app.HTTPException):
                    app.get_video(job_id)
            else:
                self.assertEqual(job['status'], 'success')
                self.assertTrue(job['safety_passed'])
                self.assertTrue(Path(app.get_video(job_id).path).exists())

    def test_prompt_guard_error_shows_only_exception_message(self):
        message = 'Qwen NSFW Guard blocked prompt: {"blocked": true, "categories": ["NSFW"], "reason": "Violation"}'
        submitted = Mock()
        submitted.json.return_value = {'prompt_id': 'blocked-prompt'}
        history = Mock()
        history.json.return_value = {'blocked-prompt': {'status': {
            'status_str': 'error',
            'messages': [
                ['execution_start', {'prompt_id': 'blocked-prompt'}],
                ['execution_error', {'exception_message': message + '\n',
                                     'traceback': ['private stack trace'], 'current_inputs': {}}],
            ],
        }}}
        app.jobs['blocked'] = {'status': 'queued'}
        with patch.object(app, 'configure_workflow', return_value={}), \
             patch.object(app.requests, 'post', return_value=submitted), \
             patch.object(app.requests, 'get', return_value=history), \
             patch.object(app, 'check_video') as checker:
            app.render_job('blocked', app.GenerateRequest(prompt='test prompt'))
        self.assertEqual(app.jobs['blocked']['message'], message)
        self.assertEqual(app.jobs['blocked']['status'], 'error')
        self.assertIsNone(app.jobs['blocked']['video_url'])
        checker.assert_not_called()

    def test_missing_error_details_uses_short_fallback(self):
        for messages in ([], None, ['invalid'], [['execution_error', {}]]):
            self.assertEqual(app.execution_error_message({'messages': messages}),
                             'ComfyUI không thể tạo video')

    def test_safe_video_can_play(self):
        self.run_render()

    def test_flagged_video_is_deleted_and_cannot_play(self):
        self.run_render(UnsafeVideoError('NSFW'))

    def test_checker_failure_cannot_play(self):
        self.run_render(RuntimeError('model unavailable'))

    def test_legacy_success_without_check_cannot_play(self):
        app.jobs['old'] = {'status': 'success', 'video_path': '/tmp/old.mp4'}
        with self.assertRaises(app.HTTPException):
            app.get_video('old')


if __name__ == '__main__':
    unittest.main()
