param(
    [string]$BackendUrl = "http://127.0.0.1:8000",
    [string]$FrontendUrl = "http://localhost:5173/"
)

$ErrorActionPreference = "Stop"

# ============================================================
# CFOx Production Acceptance Test
# ============================================================

$timestamp = Get-Date -Format "yyyyMMddHHmmss"
$testEmail = "cfox-acceptance-$timestamp@example.com"
$testPassword = "CFOx-Test-$timestamp!Aa9"

$script:Passed = 0
$script:Failed = 0
$script:Token = $null
$script:UserId = $null
$script:ConversationId = $null
$script:TransactionId = $null


function Pass-Test
{
    param([string]$Name)

    $script:Passed++

    Write-Host "[PASS] $Name" -ForegroundColor Green
}


function Fail-Test
{
    param(
        [string]$Name,
        [string]$Reason
    )

    $script:Failed++

    Write-Host "[FAIL] $Name" -ForegroundColor Red

    if ($Reason)
    {
        Write-Host "       $Reason" -ForegroundColor DarkRed
    }
}


function Invoke-CfoxRequest
{
    param(
        [ValidateSet("GET", "POST", "DELETE")]
        [string]$Method,

        [string]$Path,

        [object]$Body = $null,

        [switch]$Authenticated,

        [switch]$AllowError,

        [int]$TimeoutSec = 60
    )

    $headers = @{ }

    if ($Authenticated)
    {
        if (-not $script:Token)
        {
            throw "Authentication token is not available."
        }

        $headers["Authorization"] = "Bearer $script:Token"
    }

    $params = @{
        Method = $Method
        Uri = "$BackendUrl$Path"
        Headers = $headers
        UseBasicParsing = $true
        TimeoutSec = 60
    }

    if ($null -ne $Body)
    {
        $params["ContentType"] = "application/json"
        $params["Body"] = ($Body | ConvertTo-Json -Depth 20)
    }

    try
    {
        return Invoke-RestMethod @params
    }
    catch
    {
        if ($AllowError)
        {
            return $_
        }

        throw
    }
}


function Assert-Status
{
    param(
        [string]$Name,
        [scriptblock]$Request,
        [int[]]$ExpectedStatus = @(200)
    )

    try
    {
        $result = & $Request

        if ($result -is [System.Management.Automation.ErrorRecord])
        {
            $response = $result.Exception.Response

            if ($response)
            {
                $status = [int]$response.StatusCode

                if ($ExpectedStatus -contains $status)
                {
                    Pass-Test "$Name -> HTTP $status"
                    return $result
                }

                Fail-Test "$Name" `
                    "Expected HTTP $( $ExpectedStatus -join ', ' ), got HTTP $status."

                return $null
            }

            Fail-Test "$Name" $result.Exception.Message
            return $null
        }

        if ($ExpectedStatus -contains 200 -or
                $ExpectedStatus -contains 201 -or
                $ExpectedStatus -contains 204)
        {

            Pass-Test "$Name"
            return $result
        }

        Fail-Test "$Name" `
            "Request succeeded but expected an error status."

        return $null
    }
    catch
    {
        Fail-Test "$Name" $_.Exception.Message
        return $null
    }
}


Write-Host ""
Write-Host "============================================================"
Write-Host " CFOx PRODUCTION ACCEPTANCE TEST"
Write-Host "============================================================"
Write-Host ""
Write-Host "Backend : $BackendUrl"
Write-Host "Frontend: $FrontendUrl"
Write-Host "Test user: $testEmail"
Write-Host ""


# ============================================================
# 1. Infrastructure
# ============================================================

try
{
    $response = Invoke-WebRequest `
        -Uri "$BackendUrl/docs" `
        -UseBasicParsing `
        -TimeoutSec 15

    if ($response.StatusCode -eq 200)
    {
        Pass-Test "Backend OpenAPI endpoint"
    }
    else
    {
        Fail-Test "Backend OpenAPI endpoint" "HTTP $( $response.StatusCode )"
    }
}
catch
{
    Fail-Test "Backend OpenAPI endpoint" $_.Exception.Message
}


try
{
    $response = Invoke-WebRequest `
        -Uri $FrontendUrl `
        -UseBasicParsing `
        -TimeoutSec 15

    if ($response.StatusCode -eq 200)
    {
        Pass-Test "Frontend"
    }
    else
    {
        Fail-Test "Frontend" "HTTP $( $response.StatusCode )"
    }
}
catch
{
    Fail-Test "Frontend" $_.Exception.Message
}


# ============================================================
# 2. Unauthenticated protection
# ============================================================

try
{
    Invoke-RestMethod `
        -Method GET `
        -Uri "$BackendUrl/transactions" `
        -UseBasicParsing `
        -TimeoutSec 15

    Fail-Test "Unauthenticated /transactions rejected" `
        "Request unexpectedly succeeded."
}
catch
{
    $status = [int]$_.Exception.Response.StatusCode

    if ($status -eq 401)
    {
        Pass-Test "Unauthenticated /transactions -> HTTP 401"
    }
    else
    {
        Fail-Test "Unauthenticated /transactions" `
            "Expected HTTP 401, got HTTP $status."
    }
}


# ============================================================
# 3. Register
# ============================================================

try
{
    $registerBody = @{
        email = $testEmail
        password = $testPassword
    }

    $user = Invoke-RestMethod `
        -Method POST `
        -Uri "$BackendUrl/auth/register" `
        -Body ($registerBody | ConvertTo-Json) `
        -ContentType "application/json" `
        -UseBasicParsing `
        -TimeoutSec 30

    $script:UserId = $user.id

    if ($script:UserId)
    {
        Pass-Test "User registration"
        Write-Host "       User ID: $script:UserId"
    }
    else
    {
        Fail-Test "User registration" `
            "Response did not contain a user ID."
    }
}
catch
{
    Fail-Test "User registration" $_.Exception.Message
}


# ============================================================
# 4. Login
# ============================================================

try
{
    # IMPORTANT:
    # /auth/login uses OAuth2PasswordRequestForm.
    # Therefore the request MUST be
    # application/x-www-form-urlencoded.
    #
    # The OAuth2 field is called "username", but CFOx
    # treats that value as the user's email address.

    $loginBody = @{
        username = $testEmail
        password = $testPassword
    }

    $login = Invoke-RestMethod `
        -Method POST `
        -Uri "$BackendUrl/auth/login" `
        -Body $loginBody `
        -ContentType "application/x-www-form-urlencoded" `
        -UseBasicParsing `
        -TimeoutSec 30

    $script:Token = $login.access_token

    if ($script:Token)
    {
        Pass-Test "User login / JWT issuance"
    }
    else
    {
        Fail-Test "User login" `
            "No access token returned."
    }
}
catch
{
    Fail-Test "User login" $_.Exception.Message
}


if ($script:Token)
{

    # ========================================================
    # 5. Empty transaction list for new user
    # ========================================================

    try
    {
        $transactions = Invoke-CfoxRequest `
            -Method GET `
            -Path "/transactions" `
            -Authenticated

        if ($transactions.Count -eq 0 -or $null -eq $transactions)
        {
            Pass-Test "New user's transaction isolation"
        }
        else
        {
            Fail-Test "New user's transaction isolation" `
                "New user unexpectedly has existing transactions."
        }
    }
    catch
    {
        Fail-Test "New user's transaction isolation" $_.Exception.Message
    }


    # ========================================================
    # 6. Create transaction
    # ========================================================

    $paymentId = "cfox_acceptance_$timestamp"

    try
    {
        $transactionBody = @{
            razorpay_payment_id = $paymentId
            amount = 1000
            currency = "INR"
            status = "success"
            payment_method = "upi"
            customer_id = "cfox-acceptance-customer"
        }

        $transaction = Invoke-CfoxRequest `
            -Method POST `
            -Path "/transactions" `
            -Body $transactionBody `
            -Authenticated

        $script:TransactionId = $transaction.id

        if ($transaction.user_id -eq $script:UserId -and
                [decimal]$transaction.amount -eq 1000)
        {

            Pass-Test "Transaction creation + JWT ownership"
            Write-Host "       Transaction ID: $script:TransactionId"
        }
        else
        {
            Fail-Test "Transaction creation + JWT ownership" `
                "Transaction ownership or amount is incorrect."
        }
    }
    catch
    {
        Fail-Test "Transaction creation" $_.Exception.Message
    }


    # ========================================================
    # 7. Transaction retrieval
    # ========================================================

    try
    {
        $transactions = Invoke-CfoxRequest `
            -Method GET `
            -Path "/transactions" `
            -Authenticated

        $found = @(
        $transactions |
                Where-Object {
                    $_.razorpay_payment_id -eq $paymentId
                }
        )

        if ($found.Count -eq 1 -and
                $found[0].user_id -eq $script:UserId)
        {

            Pass-Test "Transaction retrieval"
        }
        else
        {
            Fail-Test "Transaction retrieval" `
                "Created transaction was not returned correctly."
        }
    }
    catch
    {
        Fail-Test "Transaction retrieval" $_.Exception.Message
    }


    # ========================================================
    # 8. Duplicate transaction protection
    # ========================================================

    try
    {
        $duplicateBody = @{
            razorpay_payment_id = $paymentId
            amount = 1000
            currency = "INR"
            status = "success"
            payment_method = "upi"
            customer_id = "cfox-acceptance-customer"
        }

        try
        {
            Invoke-CfoxRequest `
                -Method POST `
                -Path "/transactions" `
                -Body $duplicateBody `
                -Authenticated

            Fail-Test "Duplicate transaction protection" `
                "Duplicate transaction unexpectedly succeeded."
        }
        catch
        {
            $message = $_.Exception.Message

            if ($message -match "409")
            {
                Pass-Test "Duplicate transaction protection -> HTTP 409"
            }
            else
            {
                $response = $_.Exception.Response

                if ($response -and [int]$response.StatusCode -eq 409)
                {
                    Pass-Test "Duplicate transaction protection -> HTTP 409"
                }
                else
                {
                    Fail-Test "Duplicate transaction protection" $message
                }
            }
        }
    }
    catch
    {
        Fail-Test "Duplicate transaction protection" $_.Exception.Message
    }


    # ========================================================
    # 9. Daily revenue
    # ========================================================

    try
    {
        $dailyRevenue = Invoke-CfoxRequest `
            -Method GET `
            -Path "/transactions/analytics/daily-revenue?days=30" `
            -Authenticated

        $json = $dailyRevenue | ConvertTo-Json -Depth 20

        if ($json -match "1000")
        {
            Pass-Test "Daily revenue analytics"
        }
        else
        {
            Fail-Test "Daily revenue analytics" `
                "Created revenue was not found in the analytics response."
        }
    }
    catch
    {
        Fail-Test "Daily revenue analytics" $_.Exception.Message
    }


    # ========================================================
    # 10. Daily performance
    # ========================================================

    try
    {
        $performance = Invoke-CfoxRequest `
            -Method GET `
            -Path "/transactions/analytics/daily-performance?days=30" `
            -Authenticated

        $json = $performance | ConvertTo-Json -Depth 20

        if ($json -match '"revenue"\s*:\s*1000')
        {
            Pass-Test "Daily performance analytics"
        }
        else
        {
            Fail-Test "Daily performance analytics" `
                "Created transaction was not reflected in daily performance."
        }
    }
    catch
    {
        Fail-Test "Daily performance analytics" $_.Exception.Message
    }


    # ========================================================
    # 11. Payment-method analytics
    # ========================================================

    try
    {
        $methods = Invoke-CfoxRequest `
            -Method GET `
            -Path "/transactions/analytics/payment-methods" `
            -Authenticated

        $json = $methods | ConvertTo-Json -Depth 20

        if ($json -match "upi" -and $json -match "1000")
        {
            Pass-Test "Payment-method analytics"
        }
        else
        {
            Fail-Test "Payment-method analytics" `
                "UPI revenue was not reflected."
        }
    }
    catch
    {
        Fail-Test "Payment-method analytics" $_.Exception.Message
    }


    # ========================================================
    # 12. Dashboard
    # ========================================================

    try
    {
        $dashboard = Invoke-CfoxRequest `
            -Method GET `
            -Path "/transactions/dashboard?payment_method=upi" `
            -Authenticated

        $json = $dashboard | ConvertTo-Json -Depth 30

        if ($json -match "1000")
        {
            Pass-Test "Unified dashboard"
        }
        else
        {
            Fail-Test "Unified dashboard" `
                "Dashboard did not contain the acceptance transaction revenue."
        }
    }
    catch
    {
        Fail-Test "Unified dashboard" $_.Exception.Message
    }


    # ========================================================
    # 13. Financial health
    # ========================================================

    try
    {
        $health = Invoke-CfoxRequest `
            -Method GET `
            -Path "/transactions/analytics/financial-health" `
            -Authenticated

        if ($null -ne $health)
        {
            Pass-Test "Financial health analytics"
        }
        else
        {
            Fail-Test "Financial health analytics" `
                "Empty response."
        }
    }
    catch
    {
        Fail-Test "Financial health analytics" $_.Exception.Message
    }


    # ========================================================
    # 14. Financial actions
    # ========================================================

    try
    {
        $actions = Invoke-CfoxRequest `
            -Method GET `
            -Path "/transactions/analytics/financial-actions" `
            -Authenticated

        if ($null -ne $actions)
        {
            Pass-Test "Financial actions"
        }
        else
        {
            Fail-Test "Financial actions" `
                "Empty response."
        }
    }
    catch
    {
        Fail-Test "Financial actions" $_.Exception.Message
    }


    # ========================================================
    # 15. AI investigation
    # ========================================================

    try
    {
        $investigationBody = @{
            question = "What is my current revenue and what should I watch?"
            days = 30
        }

        $investigation = Invoke-CfoxRequest `
            -Method POST `
            -Path "/transactions/ai/investigate" `
            -Body $investigationBody `
            -Authenticated

        if ($null -ne $investigation)
        {
            Pass-Test "AI CFO investigation endpoint"
        }
        else
        {
            Fail-Test "AI CFO investigation endpoint" `
                "Empty response."
        }
    }
    catch
    {
        Fail-Test "AI CFO investigation endpoint" $_.Exception.Message
    }


    # ========================================================
    # 16. Persistent conversation creation
    # ========================================================

    try
    {
        $conversationBody = @{
            title = "Production acceptance test"
        }

        $conversation = Invoke-CfoxRequest `
        -Method POST `
        -Path "/transactions/cfo/conversations" `
        -Body $conversationBody `
        -Authenticated

        Write-Host ""
        Write-Host "========== RAW CONVERSATION RESPONSE =========="
        $conversation | ConvertTo-Json -Depth 20
        Write-Host "==============================================="
        Write-Host ""

        $script:ConversationId = $conversation.id

        if (-not $script:ConversationId)
        {
            Fail-Test "Persistent CFO conversation creation" `
            "No conversation ID was returned."
        }
        else
        {
            # Verify ownership using the authenticated detail endpoint.
            $conversationDetail = Invoke-CfoxRequest `
            -Method GET `
            -Path "/transactions/cfo/conversations/$script:ConversationId" `
            -Authenticated

            Write-Host "       Conversation ID      : $( $conversationDetail.id )"
            Write-Host "       Expected ID          : $( $script:ConversationId )"
            Write-Host "       Conversation user_id : $( $conversationDetail.user_id )"
            Write-Host "       Expected User ID     : $( $script:UserId )"

            Write-Host "       Conversation ID type : $( $conversationDetail.id.GetType().FullName )"
            Write-Host "       Expected ID type     : $( $script:ConversationId.GetType().FullName )"
            Write-Host "       Owner ID type        : $( $conversationDetail.user_id.GetType().FullName )"
            Write-Host "       Expected User type   : $( $script:UserId.GetType().FullName )"

            if (
            [int]$conversationDetail.id -eq [int]$script:ConversationId -and
                    [int]$conversationDetail.user_id -eq [int]$script:UserId
            )
            {
                Pass-Test "Persistent CFO conversation creation"

                Write-Host "       Conversation ID: $script:ConversationId"
                Write-Host "       Owner User ID: $( $conversationDetail.user_id )"
            }
            else
            {
                Fail-Test "Persistent CFO conversation creation" `
        "Conversation ownership is incorrect."
            }
        }
    }
    catch
    {
        Fail-Test "Persistent CFO conversation creation" $_.Exception.Message
    }


    if ($script:ConversationId)
    {

        # ====================================================
        # 17. Conversation listing
        # ====================================================

        try
        {
            $conversations = Invoke-CfoxRequest `
                -Method GET `
                -Path "/transactions/cfo/conversations" `
                -Authenticated

            $foundConversation = @(
            $conversations |
                    Where-Object {
                        $_.id -eq $script:ConversationId
                    }
            )

            if ($foundConversation.Count -eq 1)
            {
                Pass-Test "Persistent conversation listing"
            }
            else
            {
                Fail-Test "Persistent conversation listing" `
                    "Created conversation was not returned."
            }
        }
        catch
        {
            Fail-Test "Persistent conversation listing" $_.Exception.Message
        }


        # ====================================================
        # 18. Persistent message
        # ====================================================

        try
        {
            $messageBody = @{
                content = "What is my revenue?"
            }

            $message = Invoke-CfoxRequest `
                -Method POST `
                -Path "/transactions/cfo/conversations/$script:ConversationId/messages" `
                -Body $messageBody `
                -Authenticated

            if ($null -ne $message)
            {
                Pass-Test "Persistent CFO message"
            }
            else
            {
                Fail-Test "Persistent CFO message" `
                    "Empty response."
            }
        }
        catch
        {
            Fail-Test "Persistent CFO message" $_.Exception.Message
        }


        # ====================================================
        # 19. Conversation history
        # ====================================================

        try
        {
            $detail = Invoke-CfoxRequest `
                -Method GET `
                -Path "/transactions/cfo/conversations/$script:ConversationId" `
                -Authenticated

            $json = $detail | ConvertTo-Json -Depth 30

            if ($json -match "What is my revenue")
            {
                Pass-Test "Persistent conversation history"
            }
            else
            {
                Fail-Test "Persistent conversation history" `
                    "User message was not persisted."
            }
        }
        catch
        {
            Fail-Test "Persistent conversation history" $_.Exception.Message
        }


        # ====================================================
        # 20. Persistent streaming endpoint
        # ====================================================

        try
        {
            $streamBody = @{
                content = "Give me a short revenue summary."
            } | ConvertTo-Json

            $streamResponse = Invoke-WebRequest `
                -Method POST `
                -Uri "$BackendUrl/transactions/cfo/conversations/$script:ConversationId/messages/stream" `
                -Headers @{
                Authorization = "Bearer $script:Token"
            } `
                -ContentType "application/json" `
                -Body $streamBody `
                -UseBasicParsing `
                -TimeoutSec 120

            if ($streamResponse.StatusCode -eq 200 -and
                    $streamResponse.Content.Length -gt 0)
            {

                Pass-Test "Persistent CFO streaming endpoint"
            }
            else
            {
                Fail-Test "Persistent CFO streaming endpoint" `
                    "Empty or unsuccessful stream."
            }
        }
        catch
        {
            Fail-Test "Persistent CFO streaming endpoint" $_.Exception.Message
        }


        # ====================================================
        # 21. Delete conversation
        # ====================================================

        try
        {
            Invoke-CfoxRequest `
                -Method DELETE `
                -Path "/transactions/cfo/conversations/$script:ConversationId" `
                -Authenticated

            Pass-Test "Persistent conversation deletion"
        }
        catch
        {
            Fail-Test "Persistent conversation deletion" $_.Exception.Message
        }


        # ====================================================
        # 22. Verify deletion
        # ====================================================

        try
        {
            try
            {
                Invoke-CfoxRequest `
                    -Method GET `
                    -Path "/transactions/cfo/conversations/$script:ConversationId" `
                    -Authenticated

                Fail-Test "Deleted conversation inaccessible" `
                    "Deleted conversation was still returned."
            }
            catch
            {
                $response = $_.Exception.Response

                if ($response -and [int]$response.StatusCode -eq 404)
                {
                    Pass-Test "Deleted conversation inaccessible -> HTTP 404"
                }
                else
                {
                    Fail-Test "Deleted conversation inaccessible" `
                        $_.Exception.Message
                }
            }
        }
        catch
        {
            Fail-Test "Deleted conversation inaccessible" `
                $_.Exception.Message
        }
    }


    # ========================================================
    # 23. Legacy CFO chat
    # ========================================================

    try
    {
        $chatBody = @{
            question = "What is my revenue?"
        }

        $chatResponse = Invoke-WebRequest `
            -Method POST `
            -Uri "$BackendUrl/transactions/cfo/chat" `
            -Headers @{
            Authorization = "Bearer $script:Token"
        } `
            -ContentType "application/json" `
            -Body ($chatBody | ConvertTo-Json) `
            -UseBasicParsing `
            -TimeoutSec 120

        if ($chatResponse.StatusCode -eq 200 -and
                $chatResponse.Content.Length -gt 0)
        {

            Pass-Test "Legacy CFO chat"
        }
        else
        {
            Fail-Test "Legacy CFO chat" `
                "Empty or unsuccessful response."
        }
    }
    catch
    {
        Fail-Test "Legacy CFO chat" $_.Exception.Message
    }
}


# ============================================================
# Summary
# ============================================================

Write-Host ""
Write-Host "============================================================"
Write-Host " ACCEPTANCE TEST SUMMARY"
Write-Host "============================================================"
Write-Host ""
Write-Host "Passed: $script:Passed" -ForegroundColor Green
Write-Host "Failed: $script:Failed" -ForegroundColor Red
Write-Host ""

if ($script:Failed -eq 0)
{
    Write-Host "============================================================"
    Write-Host " CFOx PRODUCTION ACCEPTANCE TEST PASSED"
    Write-Host "============================================================"
    Write-Host ""
    Write-Host "The complete authenticated financial workflow passed."
    Write-Host ""
    exit 0
}

Write-Host "============================================================"
Write-Host " CFOx PRODUCTION ACCEPTANCE TEST FAILED"
Write-Host "============================================================"
Write-Host ""
Write-Host "Review the failed tests above."
Write-Host ""

exit 1