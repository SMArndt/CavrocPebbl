import pytest

# Tests for UI rendering functions in ui/*

def test_render_project_page(monkeypatch):
    # Stub Streamlit functions
    class DummySt:
        def __init__(self):
            self.inputs = []
            self.writes = []
        def text_input(self, label, value):
            self.inputs.append((label, value))
            return "NewProject"
        def write(self, msg):
            self.writes.append(msg)

    dummy_st = DummySt()
    # Monkey-patch st in ui.project
    import src.ui.project as project_page
    monkeypatch.setattr(project_page, 'st', dummy_st)

    # Create a simple stopex with project attribute
    class DummyProject:
        def __init__(self):
            self.project_name = "OldProject"

    class DummyStopex:
        def __init__(self):
            self.project = DummyProject()

    stopex = DummyStopex()
    project_page.render_project_page(stopex)
    # Check that the project name was updated
    assert stopex.project.project_name == "NewProject"
    # Check that the input and write calls were made
    assert dummy_st.inputs == [("Project Name", "OldProject")]
    assert dummy_st.writes == ["Optional: Company, User, etc. could go here"]


def test_render_settings_page(monkeypatch):
    # Stub Streamlit functions
    class DummySt:
        def __init__(self):
            self.selectboxes = []
            self.checkboxes = []
            self.columns_called = False
            self.expanded = False
            self.markdowns = []
            self.number_inputs = []
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False
        def subheader(self, txt):
            pass
        def columns(self, n):
            self.columns_called = True
            return (self, self)
        def selectbox(self, label, options, *args, **kwargs):
            self.selectboxes.append((label, options))
            return options[0]
        def checkbox(self, label, value=False, key=None):
            self.checkboxes.append((label, value, key))
            return True
        def expander(self, label):
            class Exp:
                def __enter__(inner):
                    return inner
                def __exit__(inner, exc_type, exc, tb):
                    return False
            self.expanded = True
            return Exp()
        def markdown(self, txt):
            self.markdowns.append(txt)
        def number_input(self, label, value=None, step=None):
            self.number_inputs.append((label, value, step))
            # return a sample numeric value
            return value or step or 1
        def file_uploader(self, *args, **kwargs):
            return None
        def text_input(self, label, value):
            return value

    dummy_st = DummySt()
    # Monkey-patch st in ui.settings
    import src.ui.settings as settings_page
    monkeypatch.setattr(settings_page, 'st', dummy_st)

    # Create simple stopex with settings attribute
    class DummySettings:
        def __init__(self):
            self.FLAC_version = None
            self.file_format = ''
            self.inc_mXrap_result = False
            self.GEM4D_output = False
            self.paraview = False
            self.import_mesh = False
            self.import_mesh_file = ''
            self.import_map3D = False
            self.import_map3D_file = ''
            self.target_zones = None
            self.farfieldzonesize = None
            self.model_boundary_offset = None
            self.zone_size_number = None
            self.zonesize_dropdown = None

    class DummyStopex:
        def __init__(self):
            self.settings = DummySettings()

    stopex = DummyStopex()
    settings_page.render_settings_page(stopex)
    # Check that selectbox and checkbox calls were made
    assert dummy_st.columns_called
    assert dummy_st.expanded
    assert dummy_st.selectboxes
    assert dummy_st.checkboxes
    assert dummy_st.number_inputs
    # Check that settings values have been updated to stub returns
    assert stopex.settings.FLAC_version == dummy_st.selectboxes[0][1][0]
    assert stopex.settings.file_format == dummy_st.selectboxes[1][1][0]
    assert stopex.settings.inc_mXrap_result is True
    assert stopex.settings.GEM4D_output is True
    assert stopex.settings.paraview is True


def test_render_generate_page(monkeypatch):
    # Stub Streamlit functions
    class DummySt:
        def __init__(self):
            self.writes = []
            self.json_calls = []
            self.markdowns = []
            self.subheaders = []
            self.downloads = []
        def write(self, msg):
            self.writes.append(msg)
        def button(self, label):
            return True
        def json(self, data):
            self.json_calls.append(data)
        def markdown(self, txt):
            self.markdowns.append(txt)
        def subheader(self, txt):
            self.subheaders.append(txt)
        def download_button(self, *args, **kwargs):
            self.downloads.append((args, kwargs))

    dummy_st = DummySt()
    # Monkey-patch st in ui.generate
    import src.ui.generate as gen_page
    monkeypatch.setattr(gen_page, 'st', dummy_st)

    # Create dummy stopex with model dump methods
    class DummyStopex:
        def __init__(self):
            self.dumpped = False
        def model_dump(self, exclude_unset=False):
            return {'a': 1}
        def model_dump_json(self, indent=0):
            return '{"a":1}'

    stopex = DummyStopex()
    gen_page.render_generate_page(stopex)
    # Check that JSON preview and download button were invoked
    assert dummy_st.json_calls[-1] == {'a': 1}
    assert dummy_st.downloads


def test_render_model_construction_page(monkeypatch):
    # Stub Streamlit functions
    class DummySt:
        def __init__(self):
            self.tabs_args = []
            self.subheaders = []
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False
        session_state = {}
        def tabs(self, titles):
            self.tabs_args.append(titles)
            # return one dummy tab for each title
            return [self] * len(titles)
        def subheader(self, txt):
            self.subheaders.append(txt)
        def checkbox(self, label, value=False, key=None, **kwargs):
            return True
        def dataframe(self, df, use_container_width, hide_index):
            pass
        def warning(self, msg):
            pass
        def plotly_chart(self, fig, use_container_width):
            pass
        def markdown(self, txt):
            pass

    dummy_st = DummySt()
    import src.ui.model_construction as mc_page
    monkeypatch.setattr(mc_page, 'st', dummy_st)
    # Stub geometry handler
    import src.ui.helpers as helpers
    monkeypatch.setattr(helpers, 'handle_geometry_section', lambda *args, **kwargs: None)

    # Create dummy stopex with minimal attributes
    class DummyMC:
        def __init__(self):
            self.topo_enabled = False
            self.dev_enabled = False
            self.hist_enabled = False
            self.aoi_enabled = False
            self.stoping_enabled = False
            self.model_construction_detail = []

    class DummySettings:
        def __init__(self):
            self.farfieldzonesize = 100

    class DummyStopex:
        def __init__(self):
            self.settings = DummySettings()
            self.model_construction = DummyMC()
            # paths used in summary
            self.session_state = {}

    stopex = DummyStopex()
    mc_page.render_model_construction_page(stopex)
    # Check that model construction flags and detail list have expected entries
    expected = ['stoping', 'topography', 'development', 'area_of_interest', 'historical']
    assert stopex.model_construction.model_construction_detail == expected
    assert stopex.model_construction.stoping_enabled is True
    assert stopex.model_construction.topo_enabled is True
    assert stopex.model_construction.dev_enabled is True
    assert stopex.model_construction.aoi_enabled is True
    assert stopex.model_construction.hist_enabled is True