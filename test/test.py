#!/usr/bin/env python
# coding: utf-8
import unittest


if __name__ == "__main__":
    import dev_appserver
    dev_appserver.fix_sys_path()
    suite = unittest.loader.TestLoader().discover('./test')
    unittest.TextTestRunner(verbosity=2).run(suite)
