{
  stdenv,
  writeTextFile,
  writeShellScriptBin,
}:

let
  # Inspired by https://github.com/NixOS/nixpkgs/blob/3dea1972737f5ce7b2c5461fe20370bad10aae03/nixos/modules/system/boot/systemd.nix#L202
  makePython3JobScriptWithPythonPackages = name: text:
    let
      x = writeTextFile { name = "unit-script.py"; executable = true; destination = "/bin/${name}"; text = "#!/usr/bin/env python3\n${text}"; };
      deriv = stdenv.mkDerivation {
        inherit name;
        unpackPhase = "true";
        installPhase = ''
          mkdir -p $out/bin
          cp ${x}/bin/${name} $out/bin/${name}
        '';
      };
    in "${deriv}/bin/${name}";
in
rec {
  pythonScript = makePython3JobScriptWithPythonPackages "iavlScript.py" ''
    import sys
    from iavl.utils import encode_stdint
    import binascii
    print("0x%s" % binascii.hexlify(encode_stdint(sys.argv[1])).decode('ascii'))
  '';

  fix_discrepancies = writeShellScriptBin "fix_discrepancies.sh" ''
    [ -z "$1" || -z "$2" ] && echo "Usage: $0 <db path> <height>
    Error: missing db path or height" && exit 1
    hex_height = $(python3 ${pythonScript}/bin/iavlScript.py $2)
    ldb --db=$1 put "s/latest" 0x08bad4d705 --value_hex
  '';
}