# ~/.config/rt/init-alpha.sh — session init for the AlphaOneSoC/FyraCore
# verification flow on the sandbox.
#
# rt runs this INSIDE the persistent remote shell whenever it creates the
# session: first use, after `rt --reset`, after the shell dies, and after the
# sandbox reboots. Keep it idempotent and fast.

set -u

# 1. Land in the verification working tree.
cd /home/mempool/AlphaOneSoC/plugins 2>/dev/null || cd /home/mempool || cd /tmp

# 2. Activate the rivercore python environment (python 3.10.16).
#    Debian 13 is PEP-668 externally-managed, so river_core/riscof/rrag all
#    live in a pyenv virtualenv rather than the system python.
export PYENV_ROOT=/home/mempool/.pyenv
case ":$PATH:" in *":$PYENV_ROOT/bin:"*) ;; *) PATH="$PYENV_ROOT/bin:$PATH" ;; esac
if command -v pyenv >/dev/null 2>&1; then
  eval "$(pyenv init -)"
  eval "$(pyenv virtualenv-init -)"
  pyenv activate rivercore 2>/dev/null || true
fi

# 3. RISC-V toolchains (rsynced from the control machine's /tools).
export ALPHA_ROOT=/home/mempool/AlphaOneSoC
for d in /home/mempool/tools/rv64-gcc-elf/bin /home/mempool/tools/rv32-isa-sim/bin; do
  [ -d "$d" ] && case ":$PATH:" in *":$d:"*) ;; *) PATH="$d:$PATH" ;; esac
done
export PATH

# 4. Services: none needed for an iverilog + spike simulation flow.

# 5. Breadcrumb so an attached human knows init ran.
echo "rt init(alpha): $(date -Is) cwd=$(pwd)" \
     "python=$(python -V 2>&1)" \
     "gcc=$(command -v riscv64-unknown-elf-gcc || echo none)" \
     "spike=$(command -v spike || echo none)" \
     "river_core=$(command -v river_core || echo none)"
