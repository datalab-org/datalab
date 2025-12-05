"""Tests for OMS (Omnistar Mass Spectrometer) file parsing and plotting"""

from pathlib import Path

import pytest

from pydatalab.apps.oms.utils import parse_oms_csv, parse_oms_dat, parse_oms_exp

OMS_DATA_DIR = Path(__file__).parent.parent.parent / "example_data" / "OMS"
OMS_TEST_FILE = OMS_DATA_DIR / "2025_11_21_kdj_354_F"


class TestOMSParsers:
    """Test OMS file parsers"""

    def test_parse_csv(self):
        """Test CSV parser returns correct columns with Time (s)"""
        csv_path = OMS_TEST_FILE.with_suffix(".csv")
        if not csv_path.exists():
            pytest.skip(f"Test file not found: {csv_path}")

        df = parse_oms_csv(csv_path)

        # Check that Time (s) column exists
        assert "Time (s)" in df.columns, "CSV should have 'Time (s)' column"

        # Check that expected species columns exist
        expected_species = ["CO2", "O2", "Ar", "CO/N2", "H2", "C2H2"]
        for species in expected_species:
            assert species in df.columns, f"Missing species column: {species}"

        # Check that we have data
        assert len(df) > 0, "CSV should contain data rows"

    def test_parse_dat(self):
        """Test DAT parser returns correct columns with Data Point"""
        dat_path = OMS_TEST_FILE.with_suffix(".dat")
        if not dat_path.exists():
            pytest.skip(f"Test file not found: {dat_path}")

        df = parse_oms_dat(dat_path)

        # Check that Data Point column exists (NOT Time (s))
        assert "Data Point" in df.columns, "DAT should have 'Data Point' column"
        assert "Time (s)" not in df.columns, "DAT should NOT have 'Time (s)' column"

        # Check that we have data
        assert len(df) > 0, "DAT should contain data rows"

    def test_parse_exp(self):
        """Test EXP parser returns position columns with no NaN values"""
        exp_path = OMS_TEST_FILE.with_suffix(".exp")
        if not exp_path.exists():
            pytest.skip(f"Test file not found: {exp_path}")

        df = parse_oms_exp(exp_path)

        # Check that timepoint column exists
        assert "timepoint" in df.columns, "EXP should have 'timepoint' column"

        # Check that position columns exist (7 positions: 0-6)
        for i in range(7):
            col_name = f"position_{i}"
            assert col_name in df.columns, f"Missing position column: {col_name}"

        # Check that we have data
        assert len(df) > 0, "EXP should contain data rows"

        # Check that there are NO NaN values (bug fix verification)
        assert df.isna().sum().sum() == 0, "EXP parser should not produce NaN values"

        # Check expected constant values (status codes)
        assert (df["position_0"] == 105).all(), "position_0 should always be 105"
        assert (df["position_1"] == 5).all(), "position_1 should always be 5"
        assert (df["position_3"] == 5).all(), "position_3 should always be 5"
        assert (df["position_4"] == 5).all(), "position_4 should always be 5"
        assert (df["position_5"] == 1).all(), "position_5 should always be 1"
        assert (df["position_6"] == 114).all(), "position_6 should always be 114"

        # Check that position_2 varies and increments by constant delta
        assert df["position_2"].nunique() > 1, "position_2 should vary"
        deltas = df["position_2"].diff().dropna()
        assert (deltas == 322).all(), "position_2 should increment by constant +322"

    def test_csv_vs_dat_data_match(self):
        """Test that species values match between CSV and DAT files"""
        csv_path = OMS_TEST_FILE.with_suffix(".csv")
        dat_path = OMS_TEST_FILE.with_suffix(".dat")

        if not csv_path.exists() or not dat_path.exists():
            pytest.skip("Both CSV and DAT test files required")

        csv_df = parse_oms_csv(csv_path)
        dat_df = parse_oms_dat(dat_path)

        # Should have same number of rows
        assert len(csv_df) == len(dat_df), "CSV and DAT should have same number of timepoints"

        # Species values should match (within floating point precision)
        species = ["CO2", "O2", "Ar", "CO/N2", "H2", "C2H2"]
        for sp in species:
            csv_vals = csv_df[sp].values
            dat_vals = dat_df[sp].values
            # Use allclose for floating point comparison
            import numpy as np

            assert np.allclose(csv_vals, dat_vals, rtol=1e-14), (
                f"{sp} values don't match between CSV and DAT"
            )

    def test_axis_label_difference(self):
        """Test that CSV uses Time (s) while DAT uses Data Point"""
        csv_path = OMS_TEST_FILE.with_suffix(".csv")
        dat_path = OMS_TEST_FILE.with_suffix(".dat")

        if not csv_path.exists() or not dat_path.exists():
            pytest.skip("Both CSV and DAT test files required")

        csv_df = parse_oms_csv(csv_path)
        dat_df = parse_oms_dat(dat_path)

        # CSV should have Time (s), DAT should have Data Point
        assert "Time (s)" in csv_df.columns, "CSV should use 'Time (s)' for x-axis"
        assert "Data Point" in dat_df.columns, "DAT should use 'Data Point' for x-axis"

        # They should be mutually exclusive
        assert "Data Point" not in csv_df.columns, "CSV should not have 'Data Point'"
        assert "Time (s)" not in dat_df.columns, "DAT should not have 'Time (s)'"

        # Data Point should be sequential, Time (s) should be real timestamps
        assert (dat_df["Data Point"] == range(len(dat_df))).all(), "Data Point should be 0, 1, 2..."
        assert csv_df["Time (s)"].iloc[1] > csv_df["Time (s)"].iloc[0], (
            "Time (s) should have real time values"
        )


class TestOMSBlock:
    """Test OMS block plotting functionality"""

    def test_block_creation(self):
        """Test that OMS block can be created"""
        from pydatalab.apps.oms import OMSBlock

        block = OMSBlock(item_id="test-id")
        assert block.blocktype == "oms"
        assert block.name == "OMS"

    def test_accepted_extensions(self):
        """Test that OMS block accepts correct file extensions"""
        from pydatalab.apps.oms import OMSBlock

        block = OMSBlock(item_id="test-id")
        assert ".csv" in block.accepted_file_extensions
        assert ".dat" in block.accepted_file_extensions
        assert ".exp" in block.accepted_file_extensions
