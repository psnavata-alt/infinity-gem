# Notice: IFPRI model code (GNU GPL v2)

The `.GMS`, `.DAT` and `.inc` files in this folder (and in the other `validation/ifpri*/gams_ph/` folders) are IFPRI's
*Extended Standard Recursive Dynamic CGE Modeling System, Version 2.00* (July 2005; Thurlow's extension of Lofgren,
Harris and Robinson 2002), taken from the public GitHub copy `uw-windc/IFPRI_model`, and released by IFPRI under the
GNU General Public License, version 2.

As condition 2 of the GPL requires, the modified files say so at the top and list the changes: the data file is a
Philippine SAM (here the full 2023 SAM; in `validation/ifpri/` and `validation/ifpri_home/` a condensed one) instead of the original South African data, and a validation block is appended at the end.
No model equation, parameter definition or calibration statement was changed.

These files are distributed under the GNU GPL v2, not under the MIT licence of the rest of this repository. The full text of
the GPL v2 is in `LICENSES/GPL-2.0-only.txt` at the root of this repository (also at
https://www.gnu.org/licenses/old-licenses/gpl-2.0.html).
