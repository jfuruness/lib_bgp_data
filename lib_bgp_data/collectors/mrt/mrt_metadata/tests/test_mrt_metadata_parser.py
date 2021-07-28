#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__authors__ = ["Tony Zheng"]
__credits__ = ["Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Production"

import pytest
from ..mrt_metadata_parser import MRT_Metadata_Parser
from ..tables import Blocks_Table, MRT_W_Metadata_Table, Distinct_Prefix_Origins_Table
from ...mrt_base.tables import MRT_Announcements_Table 
from ....roas.tables  import ROAs_Table


@pytest.fixture
def parser():
    return MRT_Metadata_Parser()

class Test_MRT_Metadata_Parser:

    def test_validate(self, parser):
        """Test empty tables raise exception."""
        with MRT_Announcements_Table(clear=True) as db:
            pass
        with ROAs_Table(clear=True) as db:
            pass
        with pytest.raises(AssertionError):
            parser._validate()

    def test_add_prefix_origin_index(self, parser):
        """Tests indexes are created if they don't exist"""
        with MRT_Announcements_Table() as t:
            indexes = [f'{t.name}_po_index', f'{t.name}_po_btree_i']
            for i in indexes:
                t.execute(f'DROP INDEX IF EXISTS {i}')
            parser._add_prefix_origin_index()
            for i in indexes:
                self.assert_index_exists(i)
    
    @pytest.mark.indexes
    def test_get_p_o_table_w_indexes(self, parser):
        """Tests that indexes exist"""
        with Distinct_Prefix_Origins_Table(clear=True) as db:
            pass
        parser._get_p_o_table_w_indexes(Distinct_Prefix_Origins_Table)
        with Distinct_Prefix_Origins_Table() as db:
            indexes = ["dpo_index", "dist_p_index", "dist_o_index", 
                        "g_index", "pbtree_index", "po_btree_index"]
            for ind in indexes:
                self.assert_index_exists_p_o(f'{db.name}_{ind}')

    @pytest.mark.block
    def test_create_block_table(self, parser):
        """Tests blocks table is filled and has indexes"""
        with Blocks_Table(clear=True) as t:
            parser._create_block_table(100)
            assert t.get_count() > 2
            for _id in ["block_id", "prefix"]:
                self.assert_index_exists(f'{t.name}_{_id}')

    @pytest.mark.roas
    def test_add_roas_index(self, parser):
        index = 'roas_index'
        self.drop_index(index)
        parser._add_roas_index()
        self.assert_index_exists(index)

    @pytest.mark.add
    def test_add_metadata(self, parser):
        parser._add_metadata()
        self.assert_index_exists(f'{MRT_W_Metadata_Table.name}_block_index')

    ########################
    ### Helper Functions ###
    ########################

    def drop_index(self, index):
        with MRT_Announcements_Table() as db:
            db.execute(f'DROP INDEX IF EXISTS {index}')

    def assert_index_exists(self, index):
        with MRT_Announcements_Table() as db:
            sql = f"SELECT indexname FROM pg_indexes WHERE indexname = '{index}'"
            assert len(db.execute(sql)) != 0
        
    def assert_index_exists_p_o(self, index):
        with Distinct_Prefix_Origins_Table() as db:
            sql = f"SELECT indexname FROM pg_indexes WHERE indexname = '{index}'"
            result = db.execute(sql)
            try:
                assert len(result) != 0
            except(AssertionError):
                print('Failed to find index for ' + index)
