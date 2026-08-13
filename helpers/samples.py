"""
Sample files for testing the three review tools.
"""

SAMPLE_VBA = '''Option Explicit

Sub ProcessData()
    Dim ws As Worksheet
    Set ws = ActiveSheet
    ws.Range("A1").Select
    Selection.Value = "Start"
    Dim i As Long
    For i = 1 To 100
        Cells(i, 1).Value = i
        Cells(i, 1).Select
    Next i
End Sub

Sub ProcessData2()
    ' Almost identical to ProcessData - redundant
    Dim ws As Worksheet
    Set ws = ActiveSheet
    Dim i As Long
    For i = 1 To 100
        Cells(i, 2).Value = i * 2
    Next i
End Sub

Sub Auto_Open()
    MsgBox "Workbook opened"
    Shell "cmd.exe /c echo test"
End Sub
'''

SAMPLE_POWERQUERY = '''let
    Source = Excel.CurrentWorkbook(){[Name="Table1"]}[Content],
    #"Changed Type" = Table.TransformColumnTypes(Source,{{"Date", type date}, {"Amount", type number}}),
    #"Filtered Rows" = Table.SelectRows(#"Changed Type", each [Amount] > 0),
    #"Added Custom" = Table.AddColumn(#"Filtered Rows", "Year", each Date.Year([Date])),
    #"Changed Type1" = Table.TransformColumnTypes(#"Added Custom",{{"Year", Int64.Type}}),
    #"Filtered Rows1" = Table.SelectRows(#"Changed Type1", each [Amount] > 0),
    #"Removed Columns" = Table.RemoveColumns(#"Filtered Rows1",{"Temp"}),
    #"Added Custom1" = Table.AddColumn(#"Removed Columns", "Year2", each Date.Year([Date]))
in
    #"Added Custom1"
'''

SAMPLE_UIPATH = '''<Activity mc:Ignorable="sap sap2010" x:Class="Main"
 xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
 xmlns:ui="http://schemas.uipath.com/workflow/activities"
 xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">
  <Sequence DisplayName="Main Sequence">
    <ui:LogMessage DisplayName="Log start" Text="Process started" />
    <ui:Delay DisplayName="Wait" Duration="00:00:05" />
    <ui:LogMessage DisplayName="Log end" Text="Process finished" />
  </Sequence>
</Activity>
'''

def get_sample_files():
    """Return a list of sample file definitions for the UI."""
    return [
        {
            "title": "VBA Sample",
            "filename": "Sample_VBA.txt",
            "content": SAMPLE_VBA,
            "caption": "Contains redundant procedures and an auto-executing macro.",
        },
        {
            "title": "Power Query Sample",
            "filename": "Sample_PowerQuery.txt",
            "content": SAMPLE_POWERQUERY,
            "caption": "Contains redundant filters and repeated column additions.",
        },
        {
            "title": "UiPath Sample",
            "filename": "Sample_UiPath.txt",
            "content": SAMPLE_UIPATH,
            "caption": "Minimal sequence with hardcoded delay.",
        },
    ]