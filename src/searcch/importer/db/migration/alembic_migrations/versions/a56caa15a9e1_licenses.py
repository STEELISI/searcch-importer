"""licenses

Revision ID: a56caa15a9e1
Revises: 8880e48a13c5
Create Date: 2021-07-22 19:14:27.723294

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


# revision identifiers, used by Alembic.
revision = 'a56caa15a9e1'
down_revision = '8880e48a13c5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    convention = {
        "uq": "uq__%(table_name)s__%(column_0_name)s",
    }
    with op.batch_alter_table('licenses', schema=None,
                              naming_convention=convention) as batch_op:
        batch_op.drop_constraint("uq__licenses__short_name")
        batch_op.add_column(sa.Column('url', sa.String(length=1024), nullable=False))
        batch_op.add_column(sa.Column('verified', sa.Boolean(), nullable=False))
        batch_op.alter_column('short_name',
               existing_type=sa.VARCHAR(length=64),
               nullable=True)
        batch_op.alter_column('long_name',
               existing_type=sa.VARCHAR(length=512),
               nullable=False)
        batch_op.create_unique_constraint(
            "uq__licenses__long_name__url__verified",
            ['long_name', 'url', 'verified'])

    # ### end Alembic commands ###
    data_upgrades()


def data_upgrades():
    my_table = table('licenses',
        column('short_name', sa.String),
        column('long_name', sa.String),
        column('url', sa.String),
        column('verified', sa.Boolean))

    op.bulk_insert(my_table,[
        {'short_name': '0BSD', 'long_name': '0-clause BSD License', 'url': 'https://opensource.org/licenses/0BSD', 'verified': True},
        {'short_name': 'BSD-1-Clause', 'long_name': '1-clause BSD License', 'url': 'https://opensource.org/licenses/BSD-1-Clause', 'verified': True},
        {'short_name': 'BSD-2-Clause', 'long_name': '2-clause BSD License', 'url': 'https://opensource.org/licenses/BSD-2-Clause', 'verified': True},
        {'short_name': 'BSD-3-Clause', 'long_name': '3-clause BSD License', 'url': 'https://opensource.org/licenses/BSD-3-Clause', 'verified': True},
        {'short_name': 'AFL-3.0', 'long_name': 'Academic Free License 3.0', 'url': 'https://opensource.org/licenses/AFL-3.0', 'verified': True},
        {'short_name': 'APL-1.0', 'long_name': 'Adaptive Public License', 'url': 'https://opensource.org/licenses/APL-1.0', 'verified': True},
        {'short_name': 'Apache-1.1', 'long_name': 'Apache Software License 1.1', 'url': 'https://opensource.org/licenses/Apache-1.1', 'verified': True},
        {'short_name': 'Apache-2.0', 'long_name': 'Apache License 2.0', 'url': 'https://opensource.org/licenses/Apache-2.0', 'verified': True},
        {'short_name': 'APSL-2.0', 'long_name': 'Apple Public Source License', 'url': 'https://opensource.org/licenses/APSL-2.0', 'verified': True},
        {'short_name': 'Artistic-1.0', 'long_name': 'Artistic license 1.0', 'url': 'https://opensource.org/licenses/Artistic-1.0', 'verified': True},
        {'short_name': 'Artistic-2.0', 'long_name': 'Artistic License 2.0', 'url': 'https://opensource.org/licenses/Artistic-2.0', 'verified': True},
        {'short_name': 'AAL', 'long_name': 'Attribution Assurance License', 'url': 'https://opensource.org/licenses/AAL', 'verified': True},
        {'short_name': 'BSL-1.0', 'long_name': 'Boost Software License', 'url': 'https://opensource.org/licenses/BSL-1.0', 'verified': True},
        {'short_name': 'BSD-2-Clause-Patent', 'long_name': 'BSD+Patent', 'url': 'https://opensource.org/licenses/BSD-2-Clause-Patent', 'verified': True},
        {'short_name': 'CECILL-2.1', 'long_name': 'CeCILL License 2.1', 'url': 'https://opensource.org/licenses/CECILL-2.1', 'verified': True},
        {'short_name': 'CDDL-1.0', 'long_name': 'Common Development and Distribution License 1.0', 'url': 'https://opensource.org/licenses/CDDL-1.0', 'verified': True},
        {'short_name': 'CPAL-1.0', 'long_name': 'Common Public Attribution License 1.0', 'url': 'https://opensource.org/licenses/CPAL-1.0', 'verified': True},
        {'short_name': 'CPL-1.0', 'long_name': 'Common Public License 1.0', 'url': 'https://opensource.org/licenses/CPL-1.0', 'verified': True},
        {'short_name': 'CATOSL-1.1', 'long_name': 'Computer Associates Trusted Open Source License 1.1', 'url': 'https://opensource.org/licenses/CATOSL-1.1', 'verified': True},
        {'short_name': 'CAL-1.0', 'long_name': 'Cryptographic Autonomy License\xa0v.1.0', 'url': 'https://opensource.org/licenses/CAL-1.0', 'verified': True},
        {'short_name': 'CUA-OPL-1.0', 'long_name': 'CUA Office Public License Version 1.0', 'url': 'https://opensource.org/licenses/CUA-OPL-1.0', 'verified': True},
        {'short_name': 'EPL-1.0', 'long_name': 'Eclipse Public License 1.0', 'url': 'https://opensource.org/licenses/EPL-1.0', 'verified': True},
        {'short_name': 'EPL-2.0', 'long_name': 'Eclipse Public License 2.0', 'url': 'https://opensource.org/licenses/EPL-2.0', 'verified': True},
        {'short_name': 'eCos-2.0', 'long_name': 'eCos License version 2.0', 'url': 'https://opensource.org/licenses/eCos-2.0', 'verified': True},
        {'short_name': 'ECL-1.0', 'long_name': 'Educational Community License, Version 1.0', 'url': 'https://opensource.org/licenses/ECL-1.0', 'verified': True},
        {'short_name': 'ECL-2.0', 'long_name': 'Educational Community License, Version 2.0', 'url': 'https://opensource.org/licenses/ECL-2.0', 'verified': True},
        {'short_name': 'EFL-1.0', 'long_name': 'Eiffel Forum License V1.0', 'url': 'https://opensource.org/licenses/EFL-1.0', 'verified': True},
        {'short_name': 'EFL-2.0', 'long_name': 'Eiffel Forum License V2.0', 'url': 'https://opensource.org/licenses/EFL-2.0', 'verified': True},
        {'short_name': 'Entessa', 'long_name': 'Entessa Public License', 'url': 'https://opensource.org/licenses/Entessa', 'verified': True},
        {'short_name': 'EUDatagrid', 'long_name': 'EU DataGrid Software License', 'url': 'https://opensource.org/licenses/EUDatagrid', 'verified': True},
        {'short_name': 'EUPL-1.2', 'long_name': 'European Union Public License 1.2', 'url': 'https://opensource.org/licenses/EUPL-1.2', 'verified': True},
        {'short_name': 'Fair', 'long_name': 'Fair License', 'url': 'https://opensource.org/licenses/Fair', 'verified': True},
        {'short_name': 'Frameworx-1.0', 'long_name': 'Frameworx License', 'url': 'https://opensource.org/licenses/Frameworx-1.0', 'verified': True},
        {'short_name': '0BSD', 'long_name': 'Free Public License 1.0.0', 'url': 'https://opensource.org/licenses/0BSD', 'verified': True},
        {'short_name': 'AGPL-3.0', 'long_name': 'GNU Affero General Public License version 3', 'url': 'https://opensource.org/licenses/AGPL-3.0', 'verified': True},
        {'short_name': 'GPL-2.0', 'long_name': 'GNU General Public License version 2', 'url': 'https://opensource.org/licenses/GPL-2.0', 'verified': True},
        {'short_name': 'GPL-3.0', 'long_name': 'GNU General Public License version 3', 'url': 'https://opensource.org/licenses/GPL-3.0', 'verified': True},
        {'short_name': 'LGPL-2.1', 'long_name': 'GNU Lesser General Public License version 2.1', 'url': 'https://opensource.org/licenses/LGPL-2.1', 'verified': True},
        {'short_name': 'LGPL-3.0', 'long_name': 'GNU Lesser General Public License version 3', 'url': 'https://opensource.org/licenses/LGPL-3.0', 'verified': True},
        {'short_name': 'HPND', 'long_name': 'Historical Permission Notice and Disclaimer', 'url': 'https://opensource.org/licenses/HPND', 'verified': True},
        {'short_name': 'IPL-1.0', 'long_name': 'IBM Public License 1.0', 'url': 'https://opensource.org/licenses/IPL-1.0', 'verified': True},
        {'short_name': 'Intel', 'long_name': 'Intel Open Source License', 'url': 'https://opensource.org/licenses/Intel', 'verified': True},
        {'short_name': 'IPA', 'long_name': 'IPA Font License', 'url': 'https://opensource.org/licenses/IPA', 'verified': True},
        {'short_name': 'ISC', 'long_name': 'ISC License', 'url': 'https://opensource.org/licenses/ISC', 'verified': True},
        {'short_name': 'jabberpl', 'long_name': 'Jabber Open Source License', 'url': 'https://opensource.org/licenses/jabberpl', 'verified': True},
        {'short_name': 'LPPL-1.3c', 'long_name': 'LaTeX Project Public License 1.3c', 'url': 'https://opensource.org/licenses/LPPL-1.3c', 'verified': True},
        {'short_name': 'BSD-3-Clause-LBNL', 'long_name': 'Lawrence Berkeley National Labs BSD Variant License', 'url': 'https://opensource.org/licenses/BSD-3-Clause-LBNL', 'verified': True},
        {'short_name': 'LiLiQ-P-1.1', 'long_name': 'Licence Libre du Québec – Permissive (LiLiQ-P) version 1.1 (LiliQ-P) ', 'url': 'https://opensource.org/licenses/LiLiQ-P-1.1', 'verified': True},
        {'short_name': 'LiLiQ-R-1.1', 'long_name': 'Licence Libre du Québec – Réciprocité (LiLiQ-R) version 1.1 (LiliQ-R)', 'url': 'https://opensource.org/licenses/LiLiQ-R-1.1', 'verified': True},
        {'short_name': 'LiLiQ-Rplus-1.1', 'long_name': 'Licence Libre du Québec – Réciprocité forte (LiLiQ-R+) version 1.1 (LiliQ-R+)', 'url': 'https://opensource.org/licenses/LiLiQ-Rplus-1.1', 'verified': True},
        {'short_name': 'LPL-1.0', 'long_name': 'Lucent Public License ("Plan9"), version 1.0 (LPL-1.0)', 'url': 'https://opensource.org/licenses/LPL-1.0', 'verified': True},
        {'short_name': 'LPL-1.02', 'long_name': 'Lucent Public License Version 1.02', 'url': 'https://opensource.org/licenses/LPL-1.02', 'verified': True},
        {'short_name': 'MS-PL', 'long_name': 'Microsoft Public License', 'url': 'https://opensource.org/licenses/MS-PL', 'verified': True},
        {'short_name': 'MS-RL', 'long_name': 'Microsoft Reciprocal License', 'url': 'https://opensource.org/licenses/MS-RL', 'verified': True},
        {'short_name': 'MirOS', 'long_name': 'MirOS Licence', 'url': 'https://opensource.org/licenses/MirOS', 'verified': True},
        {'short_name': 'MIT', 'long_name': 'MIT License', 'url': 'https://opensource.org/licenses/MIT', 'verified': True},
        {'short_name': 'MIT-0', 'long_name': 'MIT No Attribution License', 'url': 'https://opensource.org/licenses/MIT-0', 'verified': True},
        {'short_name': 'CVW', 'long_name': 'MITRE Collaborative Virtual Workspace License', 'url': 'https://opensource.org/licenses/CVW', 'verified': True},
        {'short_name': 'Motosoto', 'long_name': 'Motosoto License', 'url': 'https://opensource.org/licenses/Motosoto', 'verified': True},
        {'short_name': 'MPL-1.0', 'long_name': 'Mozilla Public License 1.0', 'url': 'https://opensource.org/licenses/MPL-1.0', 'verified': True},
        {'short_name': 'MPL-1.1', 'long_name': 'Mozilla Public License 1.1', 'url': 'https://opensource.org/licenses/MPL-1.1', 'verified': True},
        {'short_name': 'MPL-2.0', 'long_name': 'Mozilla Public License 2.0', 'url': 'https://opensource.org/licenses/MPL-2.0', 'verified': True},
        {'short_name': 'MulanPSL - 2.0', 'long_name': 'Mulan Permissive Software License v2', 'url': 'https://opensource.org/licenses/MulanPSL - 2.0', 'verified': True},
        {'short_name': 'Multics', 'long_name': 'Multics License', 'url': 'https://opensource.org/licenses/Multics', 'verified': True},
        {'short_name': 'NASA-1.3', 'long_name': 'NASA Open Source Agreement 1.3', 'url': 'https://opensource.org/licenses/NASA-1.3', 'verified': True},
        {'short_name': 'Naumen', 'long_name': 'Naumen Public License', 'url': 'https://opensource.org/licenses/Naumen', 'verified': True},
        {'short_name': 'NGPL', 'long_name': 'Nethack General Public License', 'url': 'https://opensource.org/licenses/NGPL', 'verified': True},
        {'short_name': 'Nokia', 'long_name': 'Nokia Open Source License', 'url': 'https://opensource.org/licenses/Nokia', 'verified': True},
        {'short_name': 'NPOSL-3.0', 'long_name': 'Non-Profit Open Software License 3.0', 'url': 'https://opensource.org/licenses/NPOSL-3.0', 'verified': True},
        {'short_name': 'NTP', 'long_name': 'NTP License', 'url': 'https://opensource.org/licenses/NTP', 'verified': True},
        {'short_name': 'OCLC-2.0', 'long_name': 'OCLC Research Public License 2.0', 'url': 'https://opensource.org/licenses/OCLC-2.0', 'verified': True},
        {'short_name': 'OGTSL', 'long_name': 'Open Group Test Suite License', 'url': 'https://opensource.org/licenses/OGTSL', 'verified': True},
        {'short_name': 'OSL-1.0', 'long_name': 'Open Software License 1.0', 'url': 'https://opensource.org/licenses/OSL-1.0', 'verified': True},
        {'short_name': 'OSL-2.1', 'long_name': 'Open Software License 2.1', 'url': 'https://opensource.org/licenses/OSL-2.1', 'verified': True},
        {'short_name': 'OSL-3.0', 'long_name': 'Open Software License 3.0', 'url': 'https://opensource.org/licenses/OSL-3.0', 'verified': True},
        {'short_name': 'OLDAP-2.8', 'long_name': 'OpenLDAP Public License Version 2.8', 'url': 'https://opensource.org/licenses/OLDAP-2.8', 'verified': True},
        {'short_name': 'OPL-2.1', 'long_name': 'OSET Public License version 2.1', 'url': 'https://opensource.org/licenses/OPL-2.1', 'verified': True},
        {'short_name': 'PHP-3.0', 'long_name': 'PHP License 3.0', 'url': 'https://opensource.org/licenses/PHP-3.0', 'verified': True},
        {'short_name': 'PHP-3.01', 'long_name': 'PHP License 3.01', 'url': 'https://opensource.org/licenses/PHP-3.01', 'verified': True},
        {'short_name': 'PostgreSQL', 'long_name': 'The PostgreSQL License', 'url': 'https://opensource.org/licenses/PostgreSQL', 'verified': True},
        {'short_name': 'Python-2.0', 'long_name': 'Python License', 'url': 'https://opensource.org/licenses/Python-2.0', 'verified': True},
        {'short_name': 'CNRI-Python', 'long_name': 'CNRI Python license', 'url': 'https://opensource.org/licenses/CNRI-Python', 'verified': True},
        {'short_name': 'QPL-1.0', 'long_name': 'Q Public License', 'url': 'https://opensource.org/licenses/QPL-1.0', 'verified': True},
        {'short_name': 'RPSL-1.0', 'long_name': 'RealNetworks Public Source License V1.0', 'url': 'https://opensource.org/licenses/RPSL-1.0', 'verified': True},
        {'short_name': 'RPL-1.1', 'long_name': 'Reciprocal Public License, version 1.1', 'url': 'https://opensource.org/licenses/RPL-1.1', 'verified': True},
        {'short_name': 'RPL-1.5', 'long_name': 'Reciprocal Public License 1.5', 'url': 'https://opensource.org/licenses/RPL-1.5', 'verified': True},
        {'short_name': 'RSCPL', 'long_name': 'Ricoh Source Code Public License', 'url': 'https://opensource.org/licenses/RSCPL', 'verified': True},
        {'short_name': 'OFL-1.1', 'long_name': 'SIL Open Font License 1.1', 'url': 'https://opensource.org/licenses/OFL-1.1', 'verified': True},
        {'short_name': 'SimPL-2.0', 'long_name': 'Simple Public License 2.0', 'url': 'https://opensource.org/licenses/SimPL-2.0', 'verified': True},
        {'short_name': 'Sleepycat', 'long_name': 'Sleepycat License', 'url': 'https://opensource.org/licenses/Sleepycat', 'verified': True},
        {'short_name': 'SISSL', 'long_name': 'Sun Industry Standards Source License', 'url': 'https://opensource.org/licenses/SISSL', 'verified': True},
        {'short_name': 'SPL-1.0', 'long_name': 'Sun Public License 1.0', 'url': 'https://opensource.org/licenses/SPL-1.0', 'verified': True},
        {'short_name': 'Watcom-1.0', 'long_name': 'Sybase Open Watcom Public License 1.0', 'url': 'https://opensource.org/licenses/Watcom-1.0', 'verified': True},
        {'short_name': 'UPL', 'long_name': 'Universal Permissive License', 'url': 'https://opensource.org/licenses/UPL', 'verified': True},
        {'short_name': 'NCSA', 'long_name': 'University of Illinois/NCSA Open Source License', 'url': 'https://opensource.org/licenses/NCSA', 'verified': True},
        {'short_name': 'UCL-1.0', 'long_name': 'Upstream Compatibility License v1.0', 'url': 'https://opensource.org/licenses/UCL-1.0', 'verified': True},
        {'short_name': 'unlicense', 'long_name': 'The Unlicense', 'url': 'https://opensource.org/licenses/unlicense', 'verified': True},
        {'short_name': 'VSL-1.0', 'long_name': 'Vovida Software License v. 1.0', 'url': 'https://opensource.org/licenses/VSL-1.0', 'verified': True},
        {'short_name': 'W3C', 'long_name': 'W3C License', 'url': 'https://opensource.org/licenses/W3C', 'verified': True},
        {'short_name': 'WXwindows', 'long_name': 'wxWindows Library License', 'url': 'https://opensource.org/licenses/WXwindows', 'verified': True},
        {'short_name': 'Xnet', 'long_name': 'X.Net License', 'url': 'https://opensource.org/licenses/Xnet', 'verified': True},
        {'short_name': '0BSD', 'long_name': 'Zero-Clause BSD', 'url': 'https://opensource.org/licenses/0BSD', 'verified': True},
        {'short_name': 'ZPL-2.0', 'long_name': 'Zope Public License 2.0', 'url': 'https://opensource.org/licenses/ZPL-2.0', 'verified': True},
        {'short_name': 'Zlib', 'long_name': 'zlib/libpng license', 'url': 'https://opensource.org/licenses/Zlib', 'verified': True}
    ])


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('licenses', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='unique')
        batch_op.alter_column('long_name',
               existing_type=sa.VARCHAR(length=512),
               nullable=True)
        batch_op.alter_column('short_name',
               existing_type=sa.VARCHAR(length=64),
               nullable=False)
        batch_op.drop_column('verified')
        batch_op.drop_column('url')
        batch_op.create_unique_constraint(
            "uq__short_name",
            ['short_name'])

    # ### end Alembic commands ###
