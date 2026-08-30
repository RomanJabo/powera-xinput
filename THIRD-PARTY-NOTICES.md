# Third-party notices

**This repository contains no third-party source code.** The libraries listed below are
installed by `pip` from `requirements.txt`, and the driver is installed separately by
the user. Nothing is copied into this tree, and no binaries are distributed here.

The notices are reproduced anyway, so that anyone building on this can see what they
are pulling in.

## Libraries this script runs against

None of these are contained in this repository.

| Library | License |
|---|---|
| [rene-aguirre/pywinusb](https://github.com/rene-aguirre/pywinusb) | BSD-3-Clause — Copyright (c) 2008-2012, Rene F. Aguirre |
| [yannbouteiller/vgamepad](https://github.com/yannbouteiller/vgamepad) | MIT — Copyright (c) 2021 Yann Bouteiller |
| [nefarius/ViGEmClient](https://github.com/nefarius/ViGEmClient) | MIT — Copyright (c) Nefarius Software Solutions e.U. |
| [nefarius/ViGEmBus](https://github.com/nefarius/ViGEmBus) | BSD-3-Clause — Copyright (c) Nefarius Software Solutions e.U. |

> **On the last two:** the `vgamepad` wheel ships a compiled `ViGEmClient.dll` inside
> it, so installing this project's requirements does put that binary on your disk —
> just not by way of this repository. **ViGEmBus** is a kernel-mode driver and is not
> part of any pip install at all: it has to be installed once, by hand, from its own
> releases page. Both are separate projects with their own maintainers; issues with
> either belong there, not here.

## Where the report layout came from

The byte layout in [docs/hid-report.md](docs/hid-report.md) was measured directly, with
`read_hid.py`, on one PowerA wired controller. No code, documentation or protocol table
was taken from another project.

[BetterJoy](https://github.com/Davidobot/BetterJoy) is linked from the README as the
right tool for Nintendo-branded controllers. Nothing was taken from it.

## MIT License

Applies to the two MIT-licensed entries above, each with its own copyright line as
given in the table:

```
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## BSD 3-Clause License

Applies to the two BSD-licensed entries above, each with its own copyright line as
given in the table:

```
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

 * Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.

 * Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

 * Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

## Trademarks

"Nintendo Switch" is a trademark of Nintendo, "PowerA" of Bensussen Deutsch &
Associates, and "Xbox" and "Windows" of Microsoft. They are named here and in the
documentation only to identify the hardware and interfaces this script talks to. This
project is not affiliated with, endorsed by or connected to any of them.

## This project

Everything else in this repository is MIT, see [LICENSE](LICENSE).
