"""26.715.72359 bundle 的 Linux 定点补丁。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Patch:
    label: str
    area: str
    old: str
    new: str


PATCHES = (
    Patch(
        "Linux opaque surface",
        "main",
        "function Uie({appearance:e,opaqueWindowsEnabled:t,platform:n})"
        "{return t&&!I9(e)&&(n===`darwin`||n===`win32`)}",
        "function Uie({appearance:e,opaqueWindowsEnabled:t,platform:n})"
        "{return!I9(e)&&(t||n===`linux`)}",
    ),
    Patch(
        "Linux main file manager",
        "main",
        "l1=A$({id:`fileManager`,label:`Finder`,icon:`apps/finder.png`,"
        "kind:`fileManager`,darwin:{detect:()=>`open`,args:e=>ks(e)},"
        "win32:{label:`File Explorer`,icon:`apps/file-explorer.png`,"
        "detect:u1,args:e=>ks(e),open:async({path:e})=>d1(e)}});",
        "l1=A$({id:`fileManager`,label:`Finder`,icon:`apps/finder.png`,"
        "kind:`fileManager`,darwin:{detect:()=>`open`,args:e=>ks(e)},"
        "win32:{label:`File Explorer`,icon:`apps/file-explorer.png`,"
        "detect:u1,args:e=>ks(e),open:async({path:e})=>d1(e)},"
        "linux:{label:`File Manager`,detect:()=>Ds(`xdg-open`)??`xdg-open`,"
        "args:e=>[e]}});",
    ),
    Patch(
        "Linux main editor helper",
        "main",
        "function j$({id:e,label:t,icon:n,darwinDetect:r,win32Detect:i,"
        "darwinEnv:a,darwinArgs:o,hidden:s}){return{id:e,platforms:{"
        "darwin:r?{label:t,icon:n,kind:`editor`,hidden:s,detect:r,env:a,"
        "args:o??M$,supportsSsh:!0}:void 0,win32:i?{label:t,icon:n,"
        "kind:`editor`,hidden:s,detect:i,args:M$,supportsSsh:!0}:void 0}}}",
        "function j$({id:e,label:t,icon:n,darwinDetect:r,win32Detect:i,"
        "linuxDetect:a,darwinEnv:o,darwinArgs:s,hidden:c}){return{id:e,platforms:{"
        "darwin:r?{label:t,icon:n,kind:`editor`,hidden:c,detect:r,env:o,"
        "args:s??M$,supportsSsh:!0}:void 0,win32:i?{label:t,icon:n,"
        "kind:`editor`,hidden:c,detect:i,args:M$,supportsSsh:!0}:void 0,"
        "linux:a?{label:t,icon:n,kind:`editor`,hidden:c,detect:a,args:M$,"
        "supportsSsh:!0}:void 0}}}",
    ),
    Patch(
        "Linux main VS Code",
        "main",
        "i0=j$({id:`vscode`,label:`VS Code`,icon:`apps/vscode.png`,"
        "darwinDetect:()=>S$([`/Applications/Visual Studio Code.app/Contents/"
        "Resources/app/bin/code`,`/Applications/Code.app/Contents/Resources/"
        "app/bin/code`]),win32Detect:a0});",
        "i0=j$({id:`vscode`,label:`VS Code`,icon:`apps/vscode.png`,"
        "darwinDetect:()=>S$([`/Applications/Visual Studio Code.app/Contents/"
        "Resources/app/bin/code`,`/Applications/Code.app/Contents/Resources/"
        "app/bin/code`]),win32Detect:a0,linuxDetect:()=>Ds(`code`)??`code`});",
    ),
    Patch(
        "Linux main JetBrains helper",
        "main",
        "function P1({id:e,label:t,icon:n,toolboxTarget:r,macExecutable:i,"
        "windowsPathCommands:a,windowsInstallDirPrefixes:o,"
        "windowsInstallExecutables:s,windowsFallbackPaths:c}){return{id:e,"
        "platforms:{darwin:{label:t,icon:n,kind:`editor`,detect:()=>R1(r,"
        "[`/Applications/${t}.app/Contents/MacOS/${i}`],t,i),args:V1},"
        "win32:a&&o&&s?{label:t,icon:n,kind:`editor`,detect:()=>z1({"
        "pathCommands:a,installDirPrefixes:o,installExecutables:s,"
        "fallbackPaths:c}),args:V1}:void 0}}}",
        "function P1({id:e,label:t,icon:n,toolboxTarget:r,macExecutable:i,"
        "windowsPathCommands:a,windowsInstallDirPrefixes:o,"
        "windowsInstallExecutables:s,windowsFallbackPaths:c,linuxCommand:l})"
        "{return{id:e,platforms:{darwin:{label:t,icon:n,kind:`editor`,"
        "detect:()=>R1(r,[`/Applications/${t}.app/Contents/MacOS/${i}`],t,i),"
        "args:V1},win32:a&&o&&s?{label:t,icon:n,kind:`editor`,detect:()=>z1({"
        "pathCommands:a,installDirPrefixes:o,installExecutables:s,"
        "fallbackPaths:c}),args:V1}:void 0,linux:l?{label:t,icon:n,"
        "kind:`editor`,detect:()=>Ds(l)??l,args:V1}:void 0}}}",
    ),
    Patch(
        "Linux main IntelliJ",
        "main",
        "P1({id:`intellij`,label:`IntelliJ IDEA`,icon:`apps/intellij.png`,"
        "toolboxTarget:`intellij`,macExecutable:`idea`,windowsPathCommands:"
        "[`idea64.exe`,`idea.exe`,`idea`],windowsInstallDirPrefixes:"
        "[`intellij idea`,`idea`],windowsInstallExecutables:"
        "[`idea64.exe`,`idea.exe`]})",
        "P1({id:`intellij`,label:`IntelliJ IDEA`,icon:`apps/intellij.png`,"
        "toolboxTarget:`intellij`,macExecutable:`idea`,windowsPathCommands:"
        "[`idea64.exe`,`idea.exe`,`idea`],windowsInstallDirPrefixes:"
        "[`intellij idea`,`idea`],windowsInstallExecutables:"
        "[`idea64.exe`,`idea.exe`],linuxCommand:`idea`})",
    ),
    Patch(
        "Linux main RustRover",
        "main",
        "P1({id:`rustrover`,label:`RustRover`,icon:`apps/rustrover.png`,"
        "toolboxTarget:`rustrover`,macExecutable:`rustrover`})",
        "P1({id:`rustrover`,label:`RustRover`,icon:`apps/rustrover.png`,"
        "toolboxTarget:`rustrover`,macExecutable:`rustrover`,"
        "linuxCommand:`rustrover`})",
    ),
    Patch(
        "Linux main PyCharm",
        "main",
        "P1({id:`pycharm`,label:`PyCharm`,icon:`apps/pycharm.png`,"
        "toolboxTarget:`pycharm`,macExecutable:`pycharm`,windowsPathCommands:"
        "[`pycharm64.exe`,`pycharm.exe`,`pycharm`],windowsInstallDirPrefixes:"
        "[`pycharm`],windowsInstallExecutables:[`pycharm64.exe`,`pycharm.exe`]})",
        "P1({id:`pycharm`,label:`PyCharm`,icon:`apps/pycharm.png`,"
        "toolboxTarget:`pycharm`,macExecutable:`pycharm`,windowsPathCommands:"
        "[`pycharm64.exe`,`pycharm.exe`,`pycharm`],windowsInstallDirPrefixes:"
        "[`pycharm`],windowsInstallExecutables:[`pycharm64.exe`,`pycharm.exe`],"
        "linuxCommand:`pycharm`})",
    ),
    Patch(
        "Linux main WebStorm",
        "main",
        "P1({id:`webstorm`,label:`WebStorm`,icon:`apps/webstorm.svg`,"
        "toolboxTarget:`webstorm`,macExecutable:`webstorm`,"
        "windowsPathCommands:[`webstorm64.exe`,`webstorm.exe`,`webstorm`],"
        "windowsInstallDirPrefixes:[`webstorm`],windowsInstallExecutables:"
        "[`webstorm64.exe`,`webstorm.exe`]})",
        "P1({id:`webstorm`,label:`WebStorm`,icon:`apps/webstorm.svg`,"
        "toolboxTarget:`webstorm`,macExecutable:`webstorm`,"
        "windowsPathCommands:[`webstorm64.exe`,`webstorm.exe`,`webstorm`],"
        "windowsInstallDirPrefixes:[`webstorm`],windowsInstallExecutables:"
        "[`webstorm64.exe`,`webstorm.exe`],linuxCommand:`webstorm`})",
    ),
    Patch(
        "Linux worker file manager",
        "worker",
        "sde=y9({id:`fileManager`,label:`Finder`,icon:`apps/finder.png`,"
        "kind:`fileManager`,darwin:{detect:()=>`open`,args:e=>W7(e)},"
        "win32:{label:`File Explorer`,icon:`apps/file-explorer.png`,"
        "detect:cde,args:e=>W7(e),open:async({path:e})=>lde(e)}});",
        "sde=y9({id:`fileManager`,label:`Finder`,icon:`apps/finder.png`,"
        "kind:`fileManager`,darwin:{detect:()=>`open`,args:e=>W7(e)},"
        "win32:{label:`File Explorer`,icon:`apps/file-explorer.png`,"
        "detect:cde,args:e=>W7(e),open:async({path:e})=>lde(e)},"
        "linux:{label:`File Manager`,detect:()=>U7(`xdg-open`)??`xdg-open`,"
        "args:e=>[e]}});",
    ),
    Patch(
        "Linux worker editor helper",
        "worker",
        "function b9({id:e,label:t,icon:n,darwinDetect:r,win32Detect:i,"
        "darwinEnv:a,darwinArgs:o,hidden:s}){return{id:e,platforms:{darwin:r?"
        "{label:t,icon:n,kind:`editor`,hidden:s,detect:r,env:a,args:o??x9,"
        "supportsSsh:!0}:void 0,win32:i?{label:t,icon:n,kind:`editor`,"
        "hidden:s,detect:i,args:x9,supportsSsh:!0}:void 0}}}",
        "function b9({id:e,label:t,icon:n,darwinDetect:r,win32Detect:i,"
        "linuxDetect:a,darwinEnv:o,darwinArgs:s,hidden:c}){return{id:e,"
        "platforms:{darwin:r?{label:t,icon:n,kind:`editor`,hidden:c,detect:r,"
        "env:o,args:s??x9,supportsSsh:!0}:void 0,win32:i?{label:t,icon:n,"
        "kind:`editor`,hidden:c,detect:i,args:x9,supportsSsh:!0}:void 0,"
        "linux:a?{label:t,icon:n,kind:`editor`,hidden:c,detect:a,args:x9,"
        "supportsSsh:!0}:void 0}}}",
    ),
    Patch(
        "Linux worker VS Code",
        "worker",
        "Yde=b9({id:`vscode`,label:`VS Code`,icon:`apps/vscode.png`,"
        "darwinDetect:()=>Z7([`/Applications/Visual Studio Code.app/Contents/"
        "Resources/app/bin/code`,`/Applications/Code.app/Contents/Resources/"
        "app/bin/code`]),win32Detect:Xde});",
        "Yde=b9({id:`vscode`,label:`VS Code`,icon:`apps/vscode.png`,"
        "darwinDetect:()=>Z7([`/Applications/Visual Studio Code.app/Contents/"
        "Resources/app/bin/code`,`/Applications/Code.app/Contents/Resources/"
        "app/bin/code`]),win32Detect:Xde,linuxDetect:()=>U7(`code`)??`code`});",
    ),
    Patch(
        "Linux worker JetBrains helper",
        "worker",
        "function j9({id:e,label:t,icon:n,toolboxTarget:r,macExecutable:i,"
        "windowsPathCommands:a,windowsInstallDirPrefixes:o,"
        "windowsInstallExecutables:s,windowsFallbackPaths:c}){return{id:e,"
        "platforms:{darwin:{label:t,icon:n,kind:`editor`,detect:()=>Nde(r,"
        "[`/Applications/${t}.app/Contents/MacOS/${i}`],t,i),args:N9},"
        "win32:a&&o&&s?{label:t,icon:n,kind:`editor`,detect:()=>Pde({"
        "pathCommands:a,installDirPrefixes:o,installExecutables:s,"
        "fallbackPaths:c}),args:N9}:void 0}}}",
        "function j9({id:e,label:t,icon:n,toolboxTarget:r,macExecutable:i,"
        "windowsPathCommands:a,windowsInstallDirPrefixes:o,"
        "windowsInstallExecutables:s,windowsFallbackPaths:c,linuxCommand:l})"
        "{return{id:e,platforms:{darwin:{label:t,icon:n,kind:`editor`,"
        "detect:()=>Nde(r,[`/Applications/${t}.app/Contents/MacOS/${i}`],t,i),"
        "args:N9},win32:a&&o&&s?{label:t,icon:n,kind:`editor`,detect:()=>Pde({"
        "pathCommands:a,installDirPrefixes:o,installExecutables:s,"
        "fallbackPaths:c}),args:N9}:void 0,linux:l?{label:t,icon:n,"
        "kind:`editor`,detect:()=>U7(l)??l,args:N9}:void 0}}}",
    ),
    Patch(
        "Linux worker IntelliJ",
        "worker",
        "j9({id:`intellij`,label:`IntelliJ IDEA`,icon:`apps/intellij.png`,"
        "toolboxTarget:`intellij`,macExecutable:`idea`,windowsPathCommands:"
        "[`idea64.exe`,`idea.exe`,`idea`],windowsInstallDirPrefixes:"
        "[`intellij idea`,`idea`],windowsInstallExecutables:"
        "[`idea64.exe`,`idea.exe`]})",
        "j9({id:`intellij`,label:`IntelliJ IDEA`,icon:`apps/intellij.png`,"
        "toolboxTarget:`intellij`,macExecutable:`idea`,windowsPathCommands:"
        "[`idea64.exe`,`idea.exe`,`idea`],windowsInstallDirPrefixes:"
        "[`intellij idea`,`idea`],windowsInstallExecutables:"
        "[`idea64.exe`,`idea.exe`],linuxCommand:`idea`})",
    ),
    Patch(
        "Linux worker RustRover",
        "worker",
        "j9({id:`rustrover`,label:`RustRover`,icon:`apps/rustrover.png`,"
        "toolboxTarget:`rustrover`,macExecutable:`rustrover`})",
        "j9({id:`rustrover`,label:`RustRover`,icon:`apps/rustrover.png`,"
        "toolboxTarget:`rustrover`,macExecutable:`rustrover`,"
        "linuxCommand:`rustrover`})",
    ),
    Patch(
        "Linux worker PyCharm",
        "worker",
        "j9({id:`pycharm`,label:`PyCharm`,icon:`apps/pycharm.png`,"
        "toolboxTarget:`pycharm`,macExecutable:`pycharm`,windowsPathCommands:"
        "[`pycharm64.exe`,`pycharm.exe`,`pycharm`],windowsInstallDirPrefixes:"
        "[`pycharm`],windowsInstallExecutables:[`pycharm64.exe`,`pycharm.exe`]})",
        "j9({id:`pycharm`,label:`PyCharm`,icon:`apps/pycharm.png`,"
        "toolboxTarget:`pycharm`,macExecutable:`pycharm`,windowsPathCommands:"
        "[`pycharm64.exe`,`pycharm.exe`,`pycharm`],windowsInstallDirPrefixes:"
        "[`pycharm`],windowsInstallExecutables:[`pycharm64.exe`,`pycharm.exe`],"
        "linuxCommand:`pycharm`})",
    ),
    Patch(
        "Linux worker WebStorm",
        "worker",
        "j9({id:`webstorm`,label:`WebStorm`,icon:`apps/webstorm.svg`,"
        "toolboxTarget:`webstorm`,macExecutable:`webstorm`,"
        "windowsPathCommands:[`webstorm64.exe`,`webstorm.exe`,`webstorm`],"
        "windowsInstallDirPrefixes:[`webstorm`],windowsInstallExecutables:"
        "[`webstorm64.exe`,`webstorm.exe`]})",
        "j9({id:`webstorm`,label:`WebStorm`,icon:`apps/webstorm.svg`,"
        "toolboxTarget:`webstorm`,macExecutable:`webstorm`,"
        "windowsPathCommands:[`webstorm64.exe`,`webstorm.exe`,`webstorm`],"
        "windowsInstallDirPrefixes:[`webstorm`],windowsInstallExecutables:"
        "[`webstorm64.exe`,`webstorm.exe`],linuxCommand:`webstorm`})",
    ),
    Patch(
        "Linux Open with targets",
        "webview",
        "function In({targets:e,availableTargets:t,includeHiddenTargets:n=!1,"
        "mode:r=`editor`}){let i=e.filter(e=>e.appPath!=null);if(i.length>0)"
        "return i;if(r===`native`)return e.filter(e=>e.target===`systemDefault`"
        "||e.target===`fileManager`);let a=new Set(t);return e.filter(e=>"
        "a.has(e.target)&&(n||!e.hidden))}",
        "function In({targets:e,availableTargets:t,includeHiddenTargets:n=!1,"
        "mode:r=`editor`}){let i=e.filter(e=>e.appPath!=null),a=new Set(t),"
        "o=e.filter(e=>a.has(e.target)&&(n||!e.hidden)),s=(e,t)=>e.target==="
        "t.target&&e.appPath===t.appPath,c=e=>e.filter((e,t,n)=>n.findIndex"
        "(t=>s(t,e))===t);return r===`native`?c([...i,...e.filter(e=>e.target"
        "===`systemDefault`||e.target===`fileManager`),...o]):c([...i,...o])}",
    ),
)
