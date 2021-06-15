"""
Custom Resource Lambda that manages the Greengrass service role.

Written by Nathan Slawson, 2020
"""
import sys
import logging
import boto3
from botocore.exceptions import ClientError

log = logging.getLogger('cfnGreengrass')
log.setLevel(logging.INFO)

# consoleHandler = logging.StreamHandler(sys.stdout)
# consoleHandler.setLevel(logging.INFO)
# formatter = logging.Formatter('%(asctime)s %(levelname)s - %(message)s')
# consoleHandler.setFormatter(formatter)
# log.addHandler(consoleHandler)


class ManageGreengrass:
    """
    This class creates the Greengrass Service Role if it doesn't already exist.
    """
    def __init__(self, stackName):
        self.gg = boto3.client('greengrass')
        self.iam = boto3.client('iam')
        self.roleName = 'GGServiceRole{}'.format(stackName)
        self.policyArn = 'arn:aws:iam::aws:policy/service-role/AWSGreengrassResourceAccessRolePolicy'

    def handleEvent(self, event):
        """
        Our lambda event handler
        :param event:
        :return: Usually an empty dict.
        """
        responseData = {}

        if event['RequestType'] == 'Create':
            # The only thing we do on creation is setup the greengrass service role, if needed.
            self.setupGreengrassServiceRole()
        elif event['RequestType'] == 'Delete':
            # self.resetGroupDeployments()
            self.removeGreengrassServiceRole()

        return responseData

    def getServiceRole(self):
        """
        Gets the current service role, if any.

        The reason to have getServiceRole() and getRole(), is that it's possible to have a scenario in which the
        service role associated with the account no longer exists. In this scenario, calling
        'get_server_role_for_account()' will still return the now non-existent role.
        :return:
        """
        try:
            return self.gg.get_service_role_for_account()
        except ClientError:
            return None

    def getRole(self):
        """
        Gets the current role
        :return:
        """
        try:
            return self.iam.get_role(RoleName=self.roleName)
        except self.iam.exceptions.NoSuchEntityException:
            return None

    def setupGreengrassServiceRole(self):
        """
        Sets up the Greengrass Service role.
        :return:
        """
        if not self.getServiceRole():
            serviceRole = self.getRole()
            if not self.getRole():
                serviceRole = self.iam.create_role(
                    RoleName=self.roleName,
                    AssumeRolePolicyDocument='{"Version": "2012-10-17","Statement": [{"Effect": "Allow","Principal": {"Service": "greengrass.amazonaws.com"},"Action": "sts:AssumeRole"}]}',
                    Description='Greengrass Service Role',
                )
                self.iam.attach_role_policy(
                    RoleName=self.roleName,
                    PolicyArn=self.policyArn
                )

            roleArn = serviceRole['Role']['Arn']
            self.gg.associate_service_role_to_account(RoleArn=roleArn)
            log.info('Created and associated role {}'.format(self.roleName))

    def removeGreengrassServiceRole(self):
        """
        Removes the Greengrass Service role if it exists, and if it's a role that we created previously with this
        lambda. If it's not 'ours' so to speak, we don't touch it.
        :return:
        """
        serviceRole = self.getServiceRole()
        myRole = self.getRole()
        # We double check that the service role exists, that the role still exists, and that the ARNs match
        if serviceRole and myRole and myRole['Role']['Arn'] == serviceRole['RoleArn']:
            self.gg.disassociate_service_role_from_account()
            self.iam.detach_role_policy(RoleName=self.roleName, PolicyArn=self.policyArn)
            self.iam.delete_role(RoleName=self.roleName)
            log.info('Disassociated and deleted Service Role {}'.format(self.roleName))

