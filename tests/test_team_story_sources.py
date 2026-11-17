from pathlib import Path
import unittest

from scripts.assemble_team_story import original_frame_source


class TeamStorySourceTests(unittest.TestCase):
    def setUp(self):
        self.plan = {'frozen_scene_sha256':'reviewed-opening',
                     'original_scene_patch':{'first_frame':341,'last_frame':506,
                                             'source_sha256':'finished-hands'}}
        self.base = {'source_sha256':'reviewed-opening',
                     'frame_numbers':list(range(1,178))+list(range(341,507))}
        self.patch = {'source_sha256':'finished-hands','expected_frames':166,
                      'frame_numbers':list(range(341,507))}

    def test_superseded_base_shot_cannot_fill_missing_revision(self):
        with self.assertRaisesRegex(ValueError, 'separate verified render cache'):
            original_frame_source(408,self.plan,self.base,Path('base'))

    def test_wrong_revision_is_rejected_even_when_base_has_frame(self):
        self.patch['source_sha256']='uncapped-hands'
        with self.assertRaisesRegex(ValueError, 'approved source and frame range'):
            original_frame_source(420,self.plan,self.base,Path('base'),self.patch,Path('patch'))

    def test_shortened_patch_cannot_silently_leave_old_frames(self):
        self.patch['frame_numbers']=list(range(420,507))
        self.patch['expected_frames']=87
        with self.assertRaises(ValueError):
            original_frame_source(408,self.plan,self.base,Path('base'),self.patch,Path('patch'))

    def test_opening_and_return_select_their_own_approved_sources(self):
        args=(self.plan,self.base,Path('base'),self.patch,Path('patch'))
        self.assertEqual(original_frame_source(177,*args),(Path('base'),'reviewed-opening'))
        self.assertEqual(original_frame_source(408,*args),(Path('patch'),'finished-hands'))
        self.assertEqual(original_frame_source(506,*args),(Path('patch'),'finished-hands'))


if __name__=='__main__':
    unittest.main()
