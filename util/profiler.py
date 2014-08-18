from contextlib import contextmanager
import cProfile, pstats, StringIO

@contextmanager
def profile_manager():
    pr = cProfile.Profile()
    pr.enable()

    yield

    pr.disable()
    s = StringIO.StringIO()
    sortby = 'cumulative'
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    print s.getvalue()
    
