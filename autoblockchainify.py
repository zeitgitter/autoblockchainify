#!/usr/bin/python3
#
# autoblockchainify — Automatically turn a directory into a git-based Blockchain
# (with the help of Zeitgitter timestamps and the PGP timestamping server)
#
# Copyright (C) 2019,2020 Marcel Waldvogel
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

# Main server process
#
# This is not used when installing from PyPI

import sys
sys.path.append('/usr/local/lib/python')
from autoblockchainify import daemon

daemon.run()
