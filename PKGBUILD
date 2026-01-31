# Maintainer: Ariel Baron <arielbar80@gmail.com>
pkgname=dotidx
pkgver=1.0.0
pkgrel=1
pkgdesc="A declarative, multi-profile dotfile manager focused on physical isolation and manifest-based tracking."
arch=('any')
url="https://github.com/ArielBaron/dotidx"
license=('MIT')
depends=('python' 'python-rich' 'rsync')
makedepends=('git')
source=("git+${url}.git#tag=v${pkgver}")
sha256sums=('SKIP')

package() {
  cd "$srcdir/$pkgname"

  # Create necessary directories
  install -d "$pkgdir/usr/share/dotidx"
  install -d "$pkgdir/usr/bin"

  # Install Python modules and scripts
  install -m755 dotidx.py "$pkgdir/usr/share/dotidx/dotidx.py"
  install -m644 interactive.py "$pkgdir/usr/share/dotidx/interactive.py"
  
  # Copy the shell scripts directory
  cp -r scripts "$pkgdir/usr/share/dotidx/"
  chmod +x "$pkgdir/usr/share/dotidx/scripts/"*.sh

  # Create the executable symlink in /usr/bin
  ln -s /usr/share/dotidx/dotidx.py "$pkgdir/usr/bin/dotidx"
}
