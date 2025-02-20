' 存储认证令牌
Private authToken As String
Private WithEvents inboxItems As outlook.Items

Private Sub Application_NewMailEx(ByVal EntryIDCollection As String)
    Dim mail As outlook.MailItem
    Dim ns As outlook.namespace
    Dim item As Object

    Set ns = Application.GetNamespace("MAPI")

    '
    On Error Resume Next
    Set item = ns.GetItemFromID(EntryIDCollection)
    
    ClassifyEmails
    '
'    If Not Item Is Nothing Then
'        If TypeOf Item Is outlook.MailItem Then
'            Set mail = Item
'            Call ClassifyMail(mail) '
'        End If
'    End If
End Sub




Private Sub Application_Startup()
    Set inboxItems = Session.GetDefaultFolder(olFolderInbox).Items
End Sub

Private Sub inboxItems_ItemAdd(ByVal item As Object)
    If TypeOf item Is outlook.MailItem Then
        Dim mail As outlook.MailItem
        Set mail = item
        
        MsgBox "处理新收到的邮件"
        
        ClassifyEmails
        
        ' 处理新收到的邮件
        ' 这里可以调用分类处理的代码
    End If
End Sub


' 登录并获取令牌
Private Function Login(username As String, password As String) As Boolean
    Dim loginUrl As String
    Dim requestBody As String
    Dim response As String
    
    loginUrl = "http://127.0.0.1:8000/api/auth/token/"
    requestBody = "{""username"":""" & username & """,""password"":""" & password & """}"
    
    response = CallWebAPI(loginUrl, requestBody, "POST", "")
    
    ' 解析JSON响应获取token
    If InStr(response, """token""") > 0 Then
        authToken = Split(Split(response, """")(3), """")(0)
        Login = True
    Else
        MsgBox "登录失败！", vbExclamation
        Login = False
    End If
End Function

' 修改后的CallWebAPI函数，支持认证头和HTTP方法
Private Function CallWebAPI(url As String, requestBody As String, Optional method As String = "POST", Optional token As String = "") As String
    Dim xhr As Object
    Set xhr = CreateObject("MSXML2.XMLHTTP")
    
    xhr.Open method, url, False
    xhr.setRequestHeader "Content-Type", "application/json"
    
    ' 如果提供了token，添加认证头
    If token <> "" Then
        xhr.setRequestHeader "Authorization", "Token " & token
    End If
    
    xhr.Send requestBody
    CallWebAPI = xhr.responseText
End Function

Sub ClassifyEmails()
    ' 获取收件箱
    Dim outlook As outlook.Application
    Dim namespace As outlook.namespace
    Dim inbox As outlook.Folder
    
    ' 登录获取token
    If Not Login("admin", "admin") Then
        MsgBox "认证失败，无法继续处理！", vbCritical
        Exit Sub
    End If
    
    Set outlook = Application
    Set namespace = outlook.GetNamespace("MAPI")
    Set inbox = namespace.GetDefaultFolder(olFolderInbox)
    
    ' 遍历未读邮件
    Dim mail As outlook.MailItem
    Dim apiUrl As String
    Dim requestBody As String
    Dim response As String
    
    ' 设置API地址 http://localhost:3000/api/email/content
    apiUrl = "http://127.0.0.1:8000/api/email/content/"
    
    ' 获取收件箱中的所有邮件
    Set Items = inbox.Items
    
    ' 按接收时间排序
    Items.Sort "[ReceivedTime]", True  ' True表示降序，最新的在前
    
    ' 获取最新的邮件
    If Items.Count > 0 Then
        Set mail = Items.item(1)  ' 获取第一封邮件（最新的）
        
        ' 如果是未读邮件则处理
        If mail.UnRead Then
            ' 准备请求体
'            requestBody = "{""subject"":""" & Replace(mail.Subject, """", "'") & ""","
'            requestBody = requestBody & """body"":""" & Replace(mail.Body, """", "'") & """}"
'            requestBody = "test mail content"
            requestBody = "{""subject"":""" & JsonEscape(mail.Subject) & ""","
            requestBody = requestBody & """body"":""" & JsonEscape(mail.Body) & """}"

            ' 调用API
            response = CallWebAPI(apiUrl, requestBody, "POST", authToken)
            
            ' 解析响应获取分类结果
            Dim classification As String
            classification = ParseJsonResponse(response)
            
            ' 根据分类结果处理邮件
            Select Case LCase(classification)
                Case "work"
                    mail.Categories = "工作"
                    mail.Importance = 2
                Case "festival"
                    mail.Categories = "节日"
                Case "meeting schedule"
                    mail.Categories = "会议"
                Case Else
                    mail.Categories = "其他"
            End Select
            
            ' 可以添加日志记录
            Debug.Print "Email classified as: " & classification
            
            mail.Save
            
'            ' 根据API返回结果处理邮件
'            Select Case response
'                Case """urgent"""
'                    mail.Categories = "紧急"
'                    mail.MarkAsTask olMarkComplete
'                Case """normal"""
'                    mail.Categories = "普通"
'                Case """spam"""
'                    mail.Move inbox.Folders("垃圾邮件")
'            End Select
'
'            mail.Save
        End If
    End If
    
    Set mail = Nothing
    Set Items = Nothing
    Set inbox = Nothing
    Set namespace = Nothing
    Set outlook = Nothing
End Sub

Private Function JsonEscape(text As String) As String
    Dim result As String
    result = Replace(text, "\", "\\")
    result = Replace(result, """", "\""")
    result = Replace(result, vbCrLf, "\n")
    result = Replace(result, vbCr, "\n")
    result = Replace(result, vbLf, "\n")
    JsonEscape = result
End Function

'  JSON 解析函数
Private Function ParseJsonResponse(jsonStr As String) As String
    On Error GoTo ErrorHandler
    
    ' 移除可能的换行符和多余空格
    jsonStr = Trim(jsonStr)
    
    ' 检查是否是数组格式 (以 [ 开头)
    If Left(jsonStr, 1) = "[" Then
        ' 移除首尾的 [ ]
        jsonStr = Mid(jsonStr, 2, Len(jsonStr) - 2)
    End If
    
    ' 查找 classification 字段
    Dim startPos As Long
    Dim endPos As Long
    
    startPos = InStr(1, jsonStr, """classification"":""")
    If startPos > 0 Then
        startPos = startPos + 16 ' 跳过 "classification":"
        endPos = InStr(startPos, jsonStr, "confidence")
        If endPos > startPos Then
            ParseJsonResponse = Mid(jsonStr, startPos, endPos - startPos)
            ParseJsonResponse = Replace(ParseJsonResponse, ":", "")
            ParseJsonResponse = Replace(ParseJsonResponse, ",", "")
            ParseJsonResponse = Replace(ParseJsonResponse, """", "")
        End If
    End If
    
    Exit Function

ErrorHandler:
    ParseJsonResponse = "error"
End Function

'    For Each mail In inbox.Items
'        If mail.UnRead Then
'            ' 准备请求体
'            requestBody = "{""subject"":""" & Replace(mail.Subject, """", "'") & ""","
'            requestBody = requestBody & """body"":""" & Replace(mail.Body, """", "'") & """}"
'
'            ' 调用API，传入认证令牌
'            response = CallWebAPI(apiUrl, requestBody, "POST", authToken)
'
'            ' 根据API返回结果处理邮件
'            Select Case response
'                Case """urgent"""
'                    mail.Categories = "紧急"
'                    mail.MarkAsTask olMarkComplete
'                Case """normal"""
'                    mail.Categories = "普通"
'                Case """spam"""
'                    mail.Move inbox.Folders("垃圾邮件")
'            End Select
'
'            mail.Save
'        End If
'    Next mail
'
'    Set outlook = Nothing
'    Set namespace = Nothing
'    Set inbox = Nothing
'End Sub


'Private Sub Application_ItemAdd(ByVal Item As Object)
'    MsgBox "vba got new mail " & Now
'    If TypeOf Item Is outlook.MailItem Then
'        Call AutoClassifyNewEmail(Item)
'    End If
'End Sub

'
'Sub ClassifyMail(Item As Object)
'    Dim request As Object
'    Set request = CreateObject("MSXML2.XMLHTTP")
'
'    '
'    request.Open "GET", "http://127.0.0.1:8000/api/classifier/?email=" & Item.Subject, False
'    request.Send
'
'    '
'    If request.Status = 200 Then
'        Dim response As String
'        response = request.responseText
'        If InStr(response, "Category1") > 0 Then
'            Item.Categories = "Category1"
'        Else
'            Item.Categories = "Other"
'        End If
'    End If
'    If request.Status = 401 Then
'
'        MsgBox "got request 401"
'    End If
'End Sub

