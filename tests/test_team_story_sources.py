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

    def drawing_revision(self):
        self.plan['original_scene_drawing_patch'] = {
            'first_frame':453,'last_frame':506,'source_sha256':'nib-contact'}
        return {'source_sha256':'nib-contact','expected_frames':54,
                'frame_numbers':list(range(453,507))}

    def test_completed_old_drawing_cannot_fill_missing_contact_revision(self):
        self.drawing_revision()
        with self.assertRaisesRegex(ValueError,'separate verified drawing cache'):
            original_frame_source(469,self.plan,self.base,Path('base'),self.patch,Path('patch'))

    def test_drawing_override_preserves_opening_handoff_and_new_tail(self):
        drawing=self.drawing_revision()
        args=(self.plan,self.base,Path('base'),self.patch,Path('patch'),drawing,Path('drawing'))
        self.assertEqual(original_frame_source(177,*args),(Path('base'),'reviewed-opening'))
        self.assertEqual(original_frame_source(452,*args),(Path('patch'),'finished-hands'))
        self.assertEqual(original_frame_source(453,*args),(Path('drawing'),'nib-contact'))
        self.assertEqual(original_frame_source(506,*args),(Path('drawing'),'nib-contact'))

    def test_wrong_drawing_version_is_rejected_despite_complete_older_cache(self):
        drawing=self.drawing_revision();drawing['source_sha256']='gap-drawing'
        with self.assertRaisesRegex(ValueError,'approved source and frame range'):
            original_frame_source(469,self.plan,self.base,Path('base'),self.patch,Path('patch'),drawing,Path('drawing'))

    def test_partial_drawing_cache_cannot_fall_back_to_old_tail(self):
        drawing=self.drawing_revision();drawing['frame_numbers']=list(range(453,500));drawing['expected_frames']=47
        with self.assertRaises(ValueError):
            original_frame_source(506,self.plan,self.base,Path('base'),self.patch,Path('patch'),drawing,Path('drawing'))

    def crossout_revision(self):
        self.plan['original_scene_crossout_patch'] = {
            'first_frame':71,'last_frame':118,'source_sha256':'crossout-contact'}
        return {'source_sha256':'crossout-contact','expected_frames':48,
                'frame_numbers':list(range(71,119))}

    def test_completed_opening_cannot_fill_missing_crossout_revision(self):
        self.crossout_revision()
        with self.assertRaisesRegex(ValueError,'separate verified crossout cache'):
            original_frame_source(80,self.plan,self.base,Path('base'))

    def test_crossout_override_preserves_all_other_source_boundaries(self):
        drawing=self.drawing_revision();crossout=self.crossout_revision()
        args=(self.plan,self.base,Path('base'),self.patch,Path('patch'),
              drawing,Path('drawing'),crossout,Path('crossout'))
        for frame in [70,119,177]:
            self.assertEqual(original_frame_source(frame,*args),(Path('base'),'reviewed-opening'))
        for frame in [71,80,110,118]:
            self.assertEqual(original_frame_source(frame,*args),(Path('crossout'),'crossout-contact'))
        self.assertEqual(original_frame_source(452,*args),(Path('patch'),'finished-hands'))
        self.assertEqual(original_frame_source(453,*args),(Path('drawing'),'nib-contact'))

    def test_wrong_crossout_source_cannot_reuse_complete_opening(self):
        crossout=self.crossout_revision();crossout['source_sha256']='gap-crossout'
        with self.assertRaisesRegex(ValueError,'approved source and frame range'):
            original_frame_source(80,self.plan,self.base,Path('base'),
                                  crossout_manifest=crossout,crossout_root=Path('crossout'))

    def test_partial_crossout_manifest_cannot_fall_back_to_opening(self):
        crossout=self.crossout_revision();crossout['frame_numbers']=list(range(71,118));crossout['expected_frames']=47
        with self.assertRaises(ValueError):
            original_frame_source(118,self.plan,self.base,Path('base'),
                                  crossout_manifest=crossout,crossout_root=Path('crossout'))


if __name__=='__main__':
    unittest.main()
