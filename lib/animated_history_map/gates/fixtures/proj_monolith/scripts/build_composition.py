# FIXTURE (not real code): a forbidden hand-rolled project-level compositor.
# qa_no_custom_scripts MUST flag any project-level .py when the manifest sets
# extensions.custom_scripts: false. This file is the known-bad case that proves
# the anti-monolith gate can actually fail.
print("the composition is one long timeline")  # the smell from the real failure
