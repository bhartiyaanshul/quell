# Homebrew formula for Quell
#
# This is a TEMPLATE, not yet live.  Before publishing:
#
#   1. Create a repo `bhartiyaanshul/homebrew-quell` (or `homebrew-tap`).
#   2. Copy this file to `Formula/quell.rb` in that repo.
#   3. Publish Quell to PyPI (release.yml does this on tag push).
#   4. Update `url`, `sha256`, and each dep's `sha256` in the
#      `resource` blocks below using `brew install-bottle-utility` or
#      `pypi-resources`:
#        pip install homebrew-pypi-poet
#        poet quell >> quell.rb
#      (paste the `resource` blocks it emits into the formula below.)
#
# Once live, users install with:
#
#   brew install bhartiyaanshul/quell/quell
#
# Or:
#
#   brew tap bhartiyaanshul/quell
#   brew install quell

class Quell < Formula
  include Language::Python::Virtualenv

  desc "Open-source multi-agent incident response system"
  homepage "https://github.com/bhartiyaanshul/quell"
  url "https://files.pythonhosted.org/packages/.../quell-0.2.0.tar.gz"
  sha256 "REPLACE_WITH_ACTUAL_SHA256_AFTER_PYPI_PUBLISH"
  license "Apache-2.0"

  depends_on "python@3.12"
  depends_on "git"

  # Paste `poet`-generated resource blocks here after the first PyPI release.
  # Example shape:
  #
  # resource "pydantic" do
  #   url "https://files.pythonhosted.org/packages/.../pydantic-2.9.2.tar.gz"
  #   sha256 "..."
  # end

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "quell", shell_output("#{bin}/quell --version")
    system bin/"quell", "--help"
  end
end
