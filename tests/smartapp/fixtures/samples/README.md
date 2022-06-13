These sample JSON files were taken
from the [SmartApp Lifecycles](https://developer-preview.smartthings.com/docs/connected-services/lifecycles/) page
and the [Configuration](https://developer-preview.smartthings.com/docs/connected-services/configuration/) page.

Nearly all of these samples had to be modified slightly, because the sample JSON is not actually valid.
For instance, there are illegal and/or trailing commas. I fixed the syntax errors, and in one case added a `settings`
dict (since it was empty). I also decided not to unit test the "page 2 of 2" example on the configuration
page, because I think it's wrong - it seems to be missing the `sections` entry that all of the other examples
have.

Other than that, I have left these requests as-is. The samples amount to interface documentation, since there
is not actually a formal interface spec. On the plus side, the samples that we have for events from this source
do actually line up with event interface, which I derived by looking at the code.