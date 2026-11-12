import random
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import subprocess

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import video_safety


class VideoSafetyTests(unittest.TestCase):
    def test_three_unique_frames_in_each_second_and_partial_tail(self):
        timestamps = [10 + i / 10 for i in range(24)]
        selected = video_safety.sample_frames(timestamps, random.Random(4))
        self.assertEqual(len(selected), 9)
        self.assertEqual(len(set(selected)), 9)
        for second in range(3):
            self.assertEqual(sum(int(timestamps[i] - 10) == second for i in selected), 3)

    def test_low_fps_checks_all_available_frames(self):
        self.assertEqual(video_safety.sample_frames([0, .5, 1, 1.5, 2.1]), list(range(5)))

    def test_invalid_timestamps_rejected(self):
        for values in ([], [float('nan')], [1, 0]):
            with self.assertRaises(RuntimeError):
                video_safety.sample_frames(values)

    def test_real_video_decoding_pass_block_and_inference_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'sample.mp4'
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                            'color=c=blue:s=64x64:r=10:d=2.4', '-c:v', 'mpeg4', str(path)], check=True)
            detector = Mock()
            detector.is_nsfw.return_value = False
            with patch.object(video_safety, 'get_detector', return_value=detector):
                self.assertEqual(video_safety.check_video(path), 9)
            self.assertEqual(detector.is_nsfw.call_count, 9)
            self.assertEqual(detector.is_nsfw.call_args.kwargs, {'threshold_level': 'low', 'threshold': .8})
            detector.reset_mock()
            detector.is_nsfw.side_effect = [False, True]
            with patch.object(video_safety, 'get_detector', return_value=detector):
                with self.assertRaises(video_safety.UnsafeVideoError):
                    video_safety.check_video(path)
            self.assertEqual(detector.is_nsfw.call_count, 2)
            detector.is_nsfw.side_effect = RuntimeError('inference failed')
            with patch.object(video_safety, 'get_detector', return_value=detector):
                with self.assertRaisesRegex(RuntimeError, 'inference failed'):
                    video_safety.check_video(path)

    def test_corrupt_video_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'bad.mp4'
            path.write_bytes(b'broken')
            with self.assertRaises(subprocess.CalledProcessError):
                video_safety.check_video(path)


if __name__ == '__main__':
    unittest.main()
