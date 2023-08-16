<#
    .DESCRIPTION
    Userdata init point to Invoke the download of the main.ps1 file from S3
    and run it via the function UserDataMain
#>

<powershell>
Import-Module AWSPowershell
Import-Module AutomateV2

function Start-Userdata {
    [CmdletBinding()]
    Param(
        [parameter(ValueFromPipeline)][System.Management.Automation.PSObject]$PipelineObject,
        [parameter(ValueFromPipelineByPropertyName)][String]$Task,
        [parameter(ValueFromPipelineByPropertyName)][String]$ScriptName,
        [parameter(ValueFromPipelineByPropertyName)][String]$ArtifactBucketName,
        [parameter(ValueFromPipelineByPropertyName)][String]$Role
    )
    try {
        # TODO Maybe don't download the user data every time we restart? Would reduce traffic, but convenient for making updates
        New-LogEntry -Level Info -Event "USD000" -Message "Downloading userdata library from '$ArtifactBucketName' with 'userdata/$Role' prefix"
        $ProgramFiles = [Environment]::GetEnvironmentVariable('ProgramFiles')

        #download all powershell files in the s3 folder
        Read-S3Object -BucketName $ArtifactBucketName -KeyPrefix "userdata/$Role" -Folder "$ProgramFiles\WindowsPowerShell\Modules\userdata_$Role"
        New-LogEntry -Level Info -Event "USD001" -Message "Downloaded [userdata/$Role] to [$ProgramFiles\WindowsPowerShell\Modules\userdata_$Role]"

        # import the module
        New-LogEntry -Level Info -Event "USD002" -Message "Finished downloading userdata library from '$ArtifactBucketName'"
        . "$ProgramFiles\WindowsPowerShell\Modules\userdata_$Role\main.ps1"
        Set-EnvVar -Name 'UD_USERDATALIB_DEPLOYED' -Value '1'

        # run provided main function
        New-LogEntry -Level Info -Event "USD100" -Message "Executing UserDataMain"
        $PipelineObject | Invoke-UserDataMain
        New-LogEntry -Level Info -Event "USD101" -Message "Executed UserDataMain"
    }
    catch {
        New-LogEntry -Level Fail -Event "USD999" -Message "Fatal error '$_' while executing userdata library from '$ArtifactBucketName'"
        Set-EnvVar -Name 'UD_USERDATA_ERROR' -Value $_
        Throw $_
    }

}

function Invoke {
    [CmdletBinding()]
    Param(
        [ValidateSet("Fail", "Error", "Warn", "Notice", "Info", "Debug", "Trace")][String] $LogLevel = "Debug"
    )
    PROCESS {
        $ScriptName = "^^[role]^^"
        $Task = "Initialize"
        $instance_id = Invoke-Restmethod -uri http://169.254.169.254/latest/meta-data/instance-id # Get this instance's id from the metadata service
        # Per-instance configuration updated at deploy by CDK
        New-Object -TypeName PSObject -Prop @{
            "ScriptName"           = $ScriptName
            "Task"                 = $Task
            "InstanceID"           = $instance_id
            "DomainJoinDoc"        = "^^[dc_join_doc]^^"
            "DomainName"           = "^^[domain_name]^^"
            "ArtifactBucketName"   = "^^[install_artifacts_bucket]^^"
            "Role"                 = "^^[role]^^"
            "ADUserSecret"         = "^^[ad_user_secret]^^"
            "RDSClientName"        = "^^[role]^^.^^[domain_name]^^"
            "RDCBDB"               = "^^[cb_db]^^"
            "RDSIdentifier"        = "^^[rds_identifier]^^"
            "RDSConnectionString"  = "^^[connection_string]^^"
            "ADGroupName"          = "RDS Connection Brokers"
            "SQLNCli"              = "sqlncli-11.0.msi"
            "ASGName"              = "^^[asg_name]^^"
            "SQSURL"               = "^^[sqs_url]^^"
            "DesiredASGSize"       = 2
        } | Execute-AutomateScript -ScriptName $ScriptName -TaskFunction (Get-Item function:Start-Userdata) -LogLevel $LogLevel
    }
}

Invoke
</powershell>
<persist>true</persist>
