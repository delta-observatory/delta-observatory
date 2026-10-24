#!/bin/sh
# Run inside the selected Linux build environment. The output contains no live state.
set -eu
release_dir=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
source_dir="$release_dir/.build/sources"
payload_dir="$release_dir/.build/payload"
uv_bin=${DELTA_BUILD_UV:-uv}
export UV_CACHE_DIR="$release_dir/.cache/uv"
export UV_PYTHON_INSTALL_DIR="$release_dir/.build/python-install"
export PYTHONDONTWRITEBYTECODE=1

test -f "$source_dir/sources.json"
test ! -e "$payload_dir"
mkdir -p "$payload_dir"
"$uv_bin" python install 3.12.14 --no-bin --no-config
cp -a "$UV_PYTHON_INSTALL_DIR/cpython-3.12.14-linux-x86_64-gnu" "$payload_dir/python"
python_bin="$payload_dir/python/bin/python3.12"

# The API and worker pins differ. Separate targets preserve both environments.
"$uv_bin" pip install --python "$python_bin" --target "$payload_dir/api-packages" \
    --require-hashes -r "$source_dir/backend/requirements.txt"
"$uv_bin" pip install --python "$python_bin" --target "$payload_dir/worker-packages" \
    -r "$source_dir/workers/requirements.txt"

mkdir -p "$payload_dir/components" "$payload_dir/notices"
for component in backend workers; do
    mkdir -p "$payload_dir/components/$component"
    cp -a "$source_dir/$component/src" "$source_dir/$component/vendor" "$payload_dir/components/$component/"
    cp "$source_dir/$component/LICENSE" "$payload_dir/notices/$component-LICENSE"
    cp "$source_dir/$component/requirements.txt" "$payload_dir/notices/$component-requirements.txt"
done
mkdir -p "$payload_dir/components/agents"
cp -a "$source_dir/agents/adapter" "$source_dir/agents/managed" "$payload_dir/components/agents/"
cp "$source_dir/agents/LICENSE" "$payload_dir/notices/agents-LICENSE"
mkdir -p "$payload_dir/components/database"
cp -a "$source_dir/database/migrations" "$source_dir/database/migrate.sh" "$payload_dir/components/database/"
cp "$source_dir/database/LICENSE" "$payload_dir/notices/database-LICENSE"
cp "$source_dir/sources.json" "$payload_dir/sources.json"
cp -a "$release_dir/resources/catalog" "$payload_dir/catalog"

postgres_archive="$release_dir/.cache/postgresql-18.6.tar.bz2"
printf '%s  %s\n' '555610c24d53e4316da5b7d3fc25c279d96856d5e0e23ee308c328c5fa881d9f' "$postgres_archive" | sha256sum -c -
mkdir -p "$release_dir/.build/postgres-source"
tar -xjf "$postgres_archive" -C "$release_dir/.build/postgres-source" --strip-components=1
cd "$release_dir/.build/postgres-source"
# A private Unix socket needs no TLS, readline, ICU, or compression libraries.
./configure --prefix="$payload_dir/postgres" --without-readline --without-zlib --without-icu \
    --without-lz4 --without-zstd > "$release_dir/.build/postgres-configure.log" 2>&1
make -j4 > "$release_dir/.build/postgres-make.log" 2>&1
make install > "$release_dir/.build/postgres-install.log" 2>&1
cp COPYRIGHT "$payload_dir/notices/PostgreSQL-COPYRIGHT"
printf '%s\n' 'https://ftp.postgresql.org/pub/source/v18.6/postgresql-18.6.tar.bz2' > "$payload_dir/notices/PostgreSQL-SOURCE"
"$payload_dir/postgres/bin/postgres" --version
"$python_bin" --version
