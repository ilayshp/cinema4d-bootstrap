// generated by bootstrap for c4d version 1.0
CONTAINER Tmyplugin
{
    NAME Tmyplugin;
    INCLUDE Tbase;
    INCLUDE Texpression;
    GROUP GROUP_BASE_SETTINGS
    {
        DEFAULT 1;
        REAL STRENGTH
        {
            MIN 0.0;
            MAX 100.0;
            MINSLIDER 0.0;
            MAXSLIDER 100.0;
            STEP 1.0;
            UNIT PERCENT;
            CUSTOMGUI REALSLIDER;
        }
    }
}