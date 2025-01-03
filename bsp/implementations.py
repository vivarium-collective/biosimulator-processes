STEP_IMPLEMENTATIONS = [
    ('output-generator', 'main.OutputGenerator'),
    ('time-course-output-generator', 'main.TimeCourseOutputGenerator'),
    ('smoldyn_step', 'main.SmoldynStep'),
    ('simularium_smoldyn_step', 'main.SimulariumSmoldynStep'),
    ('mongo-emitter', 'main.MongoDatabaseEmitter'),
    ('copasi-step', 'ode_simulation.CopasiStep'),
    ('tellurium-step', 'ode_simulation.TelluriumStep'),
    ('amici-step', 'ode_simulation.AmiciStep'),
    ('plotter', 'viz.CompositionPlotter'),
    ('plotter2d', 'viz.Plotter2d'),
    ('utc-comparator', 'comparator_step.UtcComparator'),
    ('smoldyn-step', 'bio_compose.SmoldynStep'),
    ('simularium-smoldyn-step', 'bio_compose.SimulariumSmoldynStep'),
    ('database-emitter', 'bio_compose.MongoDatabaseEmitter')
]


PROCESS_IMPLEMENTATIONS = [
    ('cobra-process', 'cobra_process.CobraProcess'),
    ('copasi-process', 'copasi_process.CopasiProcess'),
    ('tellurium-process', 'tellurium_process.TelluriumProcess'),
    ('utc-amici', 'amici_process.UtcAmici'),
    ('utc-copasi', 'copasi_process.UtcCopasi'),
    ('utc-tellurium', 'tellurium_process.UtcTellurium')
]